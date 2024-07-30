import json
import logging
from typing import Union, Optional, List, Dict
import gitlab
from gitlab.v4.objects import Project, ProjectTrigger


logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITLAB_PA_TOKEN = "GITLAB_PA_TOKEN"


class GccLzQA(object):
    def __init__(self,
                 gitlab_host: str,
                 gitlab_pa_token: str,
                 gcc_lz_repo: str,
                 feat_ticket: str,
                 testing_repos: List[object],
                 ssl_verify: bool = False):

        self.gl = gitlab.Gitlab(
            url=gitlab_host,
            private_token=gitlab_pa_token,
            ssl_verify=ssl_verify)

        self.feat_ticket = feat_ticket
        self._gcc_lz_repo = self.gl.projects.get(gcc_lz_repo)
        self._testing_repos = {env: {} for env in testing_repos}

        for env, v in testing_repos.items():
            # get repo project
            project = self.gl.projects.get(f'{v["grp"]}{v["prj"]}')
            self._testing_repos[env]['project'] = project

            # get main branch
            main_branch = self._get_main_branch(project)
            self._testing_repos[env]['main_branch'] = main_branch

            # get pipeline trigger
            trigger = self._get_pipeline_trigger(project)
            self._testing_repos[env]['trigger'] = trigger

        logger.info(f'Start QA [{self.feat_ticket}] on {self.testing_repos}')

    @property
    def testing_repos(self) -> List[str]:
        return [v['project'].name for k, v in self._testing_repos.items()]

    @property
    def gcc_lz_repo(self) -> Project:
        return self._gcc_lz_repo

    def setup_feat_branch(self) -> None:
        for k, v in self._testing_repos.items():
            logger.info(
                f'{v["project"].name}: Create [{self.feat_ticket}] branch')
            project = v['project']
            main_branch = v['main_branch']

            # get/create feat branch
            self._create_feat_branch(project, main_branch)

            # add lz config file
            self._commit_lz_config(project)

            # set default branch to feature
            logger.info(
                f'{v["project"].name}: Set [{self.feat_ticket}] as default')
            project.default_branch = self.feat_ticket
            project.save()

        return

    def trigger_testing_pipeline(self) -> None:
        for k, v in self._testing_repos.items():
            project = v['project']

            # create trigger if not existed
            if v['trigger'] is None:
                v['trigger'] = self._create_pipeline_trigger(project)

            # trigger pipeline for feature branch
            v['pipeline'] = self._trigger_pipeline(
                v['project'], v['trigger'].token, self.feat_ticket)
        return

    def trigger_main_pipeline(self) -> None:
        for k, v in self._testing_repos.items():
            project = v['project']

            # create trigger if not existed
            if v['trigger'] is None:
                v['trigger'] = self._create_pipeline_trigger(project)

            # trigger pipeline for main branch
            v['pipeline'] = self._trigger_pipeline(
                v['project'], v['trigger'].token, v['main_branch'])
        return

    def delete_temp_pipeline_trigger(self) -> None:
        '''
        clean up: delete temporary pipeline trigger token
        '''
        for k, v in self._testing_repos.items():
            trigger = v['trigger']
            if trigger:
                logger.info(
                    f'{v["project"].name}: Trigger found and deleted.')
                trigger.delete()
            else:
                logger.info(f'{v["project"].name}: Trigger not found.')

        return

    def reset_default_branch(self) -> None:
        '''
        clean up: reset default branch to main
        '''
        for k, v in self._testing_repos.items():
            v['project'].default_branch = v['main_branch']
            v['project'].save()
            logger.info(f'{v["project"].name}: Default branch reset.')
        return

    def delete_feat_branch(self) -> None:
        '''
        clean up: delete feature branch
        '''
        for k, v in self._testing_repos.items():
            try:
                v['project'].branches.get(self.feat_ticket).delete()
                logger.info(
                    f'{v["project"].name}: [{self.feat_ticket}] found and deleted.')
            except (gitlab.exceptions.GitlabHttpError, gitlab.exceptions.GitlabGetError) as ex:
                logger.info(
                    f'{v["project"].name}: [{self.feat_ticket}] not found.')
        return

    def output(self):
        output = []
        for k, v in self._testing_repos.items():
            output.append({
                "environment": k,
                "pipeline_url": v['pipeline'].web_url if v['pipeline'] else None,
                "repo_url": v['project'].web_url
            })
        print(json.dumps(output, indent=2))
        return output

    def pre_checks(self) -> List[str]:
        checks = []
        # feat branch is not wrongly set as main or master or empty
        if self.feat_ticket in ('', 'main', 'master'):
            checks.append(f'WRONG feat branch configured: {self.feat_ticket}')

        # test repo default branch is not used by others
        for k, v in self._testing_repos.items():
            if v['project'].default_branch not in ('main', 'master', self.feat_ticket):
                checks.append(
                    f'Default branch [{v["project"].default_branch}] is in use by others.')

        # Confirm feat branch exist in lz repo
        try:
            self._gcc_lz_repo.branches.get(self.feat_ticket)
        except (gitlab.exceptions.GitlabGetError, gitlab.exceptions.GitlabParsingError) as ex:
            checks.append(
                f'Feat branch [{self.feat_ticket}] not found in LZ repo')

        return checks

    def _get_main_branch(self, gl_project: Project) -> str:
        branches = gl_project.protectedbranches.list()
        return "main" if "main" in branches else "master"

    def _create_feat_branch(self, gl_project: Project, main_branch: str) -> str:
        try:
            feat_branch = gl_project.branches.get(self.feat_ticket)
            logger.info(f'{gl_project.name}: Feat branch existed.')
        except gitlab.exceptions.GitlabGetError as ex:
            feat_branch = gl_project.branches.create(
                {'branch': self.feat_ticket, 'ref': main_branch})
            logger.info(
                f'{gl_project.name}: Feat branch not found, created.')
        return feat_branch.name

    def _commit_lz_config(self, gl_project: Project) -> None:
        lz_config_path = '.lz_config.yml'
        try:
            gl_project.files.get(lz_config_path, self.feat_ticket)
            action = "update"
            logger.info(f'{gl_project.name}: lz_config existed.')
        except gitlab.exceptions.GitlabGetError as ex:
            action = "create"
            logger.info(f'{gl_project.name}: lz_config not found.')

        try:
            data = {
                'branch': self.feat_ticket,
                'commit_message': f'test {self.feat_ticket}',
                'actions': [
                    {
                        'action': action,
                        'file_path': lz_config_path,
                        'content': f'.lz_version: {self.feat_ticket}',
                    },
                ]
            }
            commit = gl_project.commits.create(data)
            logger.info(f'{gl_project.name}: .lz_config updated/created.')
        except gitlab.exceptions.GitlabCreateError as ex:
            logger.warning(f'{gl_project.name}: Fail to commit lz_config.yml')
        return

    def _get_pipeline_trigger(self, gl_project: Project) -> Union[ProjectTrigger, None]:
        trigger = None
        trigger_desc = f'temp token to test {self.feat_ticket}'
        for t in gl_project.triggers.list():
            if t.description == trigger_desc:
                trigger = t
                logger.info(f'{gl_project.name}: Trigger existed.')
                break
        if trigger is None:
            logger.info(f'{gl_project.name}: Trigger not found.')
        return trigger

    def _create_pipeline_trigger(self, gl_project: Project) -> ProjectTrigger:
        trigger_desc = f'temp token to test {self.feat_ticket}'
        trigger = gl_project.triggers.create({'description': trigger_desc})
        logger.info(f'{gl_project.name}: Trigger created.')
        return trigger

    def _trigger_pipeline(self, gl_project: Project, trigger_token: str, ref: str) -> None:
        try:
            pipeline = gl_project.trigger_pipeline(
                ref=ref,
                token=trigger_token,
                variables={
                    "POLICY_MATCH_TYPE": "",
                    "POLICY_LIST": "[]"
                })
            logger.info(f'{gl_project.name}: [{ref}] Pipeline triggered.')
        except gitlab.exceptions.GitlabCreateError as ex:
            logger.info(f'{gl_project.name}: [{ref}]Fail to trigger pipeline.')
            raise ex

        return pipeline


def deploy_a_feature_branch_to_project(branch, project) -> str:
    '''
    args
        branch (str): the git repo feature branch to be deployed
        project (str): the target git project to deploy the feature branch to
    '''
    try:
        qa_feat = GccLzQA(
            gitlab_host="https://sgts.gitlab-dedicated.com/",
            gitlab_pa_token=GITLAB_PA_TOKEN,
            gcc_lz_repo="wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz/aws-tlz-landingzones/aws-landingzones",
            testing_repos={
                "gcc2_dev": {
                    "grp": "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz-dev/agency-baseline/dev/gvt/",
                    # "gcci-agency-gvt-gcc-monitoring-dev-baseline",
                    "prj": project
                }
            },
            feat_ticket=branch,  # <== Use this ticket id as branch name,
            ssl_verify=False,  # Set False if cloudflare is on
        )
        if (checks := qa_feat.pre_checks()) != []:
            logger.warning("\n".join(checks))
            ret = ", ".join(checks)
        else:
            qa_feat.setup_feat_branch()
            qa_feat.trigger_testing_pipeline()
            ret = qa_feat.output()
    except Exception as error:
        ret = f"Fail to deploy due to error {str(error)}"

    return ret


def reset_project_to_main_branch(branch, project) -> str:
    '''
    args
        branch (str): the feature branch
        project (str): the target project to restore to main branch
    '''
    try:
        qa_feat = GccLzQA(
            gitlab_host="https://sgts.gitlab-dedicated.com/",
            gitlab_pa_token=GITLAB_PA_TOKEN,
            gcc_lz_repo="wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz/aws-tlz-landingzones/aws-landingzones",
            testing_repos={
                "gcc2_dev": {
                    "grp": "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz-dev/agency-baseline/dev/gvt/",
                    # "gcci-agency-gvt-gcc-monitoring-dev-baseline",
                    "prj": project
                }
            },
            feat_ticket=branch,  # <== Use this ticket id as branch name,
            ssl_verify=False,  # Set False if cloudflare is on
        )
        if (checks := qa_feat.pre_checks()) != []:
            logger.warning("\n".join(checks))
            ret = ", ".join(checks)
        else:
            qa_feat.reset_default_branch()
            qa_feat.delete_feat_branch()
            qa_feat.trigger_main_pipeline()
            qa_feat.delete_temp_pipeline_trigger()
            ret = qa_feat.output()
    except Exception as error:
        ret = f"Fail to deploy due to error {str(error)}"

    return ret
