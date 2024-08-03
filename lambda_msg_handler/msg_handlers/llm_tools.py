import logging
import os
import json
from datetime import datetime, timezone

from msg_handlers.aws_related.utils import find_account_details, list_account_scps, create_a_gen_vpc, find_subscription_details
from msg_handlers.gitlab_related.gcc_lz_qa import deploy_a_feature_branch_to_project, reset_project_to_main_branch

logger = logging.getLogger()
logger.setLevel(logging.INFO)

llm_tools_vars = json.loads(
    os.environ.get('llm_tools_vars', '{}')
)


def find_birthday(**args) -> str:
    name = args['name']
    bd = "unknown"
    if "yangbo" in name.lower():
        bd = "1991.Aug"
    return bd


def current_datetime(**args) -> str:
    return datetime.now(timezone.utc).isoformat()


def aws_find_account_details(**args) -> str:
    return find_account_details(llm_tools_vars['iamr_gcc2dev_org'], args["account_id"])


def aws_list_account_scps(**args) -> str:
    return list_account_scps(llm_tools_vars['iamr_gcc2dev_org'], args["account_id"])


def azure_find_subscription_details(**args) -> str:
    return find_subscription_details(llm_tools_vars['iamr_gcc2dev_css'], args["subscription_id"])


def aws_create_a_gen_vpc(**args) -> str:
    return create_a_gen_vpc(llm_tools_vars['iamr_demo_acct'], args["name"], args["cidr_block"])


def gitlab_deploy_a_feature_branch_to_project(**args) -> str:
    gitlab_grp = {
        "gccplus_stg": "wog/gvt/gccplus/gvt-gccplus/provisioning/tlz-stg/agency-baseline/stg/gvt/",
        "gccplus_prd": "wog/gvt/gccplus/gvt-gccplus/provisioning/tlz/agency-baseline/prod/gvt/",
        "gcc2_dev": "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz-dev/agency-baseline/dev/gvt/",
        "gcc2_prd":  "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz/agency-baseline/prod/gvt/",
    }
    return deploy_a_feature_branch_to_project(
        args["branch"], args['gcc_env'], gitlab_grp[args['gcc_env']],  args["project"],
        llm_tools_vars['gitlab_pa_token'], llm_tools_vars['gitlab_host'], llm_tools_vars['gcc_lz_repo'])


def gitlab_reset_project_to_main_branch(**args) -> str:
    gitlab_grp = {
        "gccplus_stg": "wog/gvt/gccplus/gvt-gccplus/provisioning/tlz-stg/agency-baseline/stg/gvt/",
        "gccplus_prd": "wog/gvt/gccplus/gvt-gccplus/provisioning/tlz/agency-baseline/prod/gvt/",
        "gcc2_dev": "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz-dev/agency-baseline/dev/gvt/",
        "gcc2_prd":  "wog/gvt/gcc/gcc2.0/gcc-provisioning-squad/tlz/agency-baseline/prod/gvt/",
    }
    return reset_project_to_main_branch(
        args["branch"], args['gcc_env'], gitlab_grp[args['gcc_env']],  args["project"],
        llm_tools_vars['gitlab_pa_token'], llm_tools_vars['gitlab_host'], llm_tools_vars['gcc_lz_repo'])


tools = {
    "definitions": [
        {
            "type": "function",
            "function": {
                "name": "find_birthday",
                "description": "Get the birth date of a person.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the person."
                        },
                    },
                    "required": ["name"],
                },
            },
        }, {
            "type": "function",
            "function": {
                "name": "current_datetime",
                "description": "Find current date time in UTC.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }, {
            "type": "function",
            "function": {
                "name": "aws_find_account_details",
                "description": "Find the AWS account name, root email, account status and other info about an AWS account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "AWS Account id, format is always a 12-digit numeric string."
                        },
                    },
                    "required": ["account_id"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "aws_list_account_scps",
                "description": "List out the policies that have been imposed on the AWS account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "AWS Account id, format is always a 12-digit numeric string."
                        },
                    },
                    "required": ["account_id"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "azure_find_subscription_details",
                "description": "Find the owner, tenant details and git repo of an azure subscription by subscription id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "Azure Subscription id, format is always a 36 character string with alphanumeric and hyphen."
                        },
                    },
                    "required": ["subscription_id"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "aws_create_a_gen_vpc",
                "description": "This function will create a VPC with the specified name and the CIDR range block",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the VPC to be created."
                        },
                        "cidr_block": {
                            "type": "string",
                            "description": "The network CIDR range block for the VPC. For example, 172.0.0.0/26"
                        },
                    },
                    "required": ["name", "cidr_block"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "gitlab_deploy_a_feature_branch_to_project",
                "description": "This function will trigger a gitlab pipeline to deploy the feature branch for the git project. The output is the link to the deployment pipeline. Please always ask user for input if not clear, and always double confirm with user before running this function.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "The git repo feature branch to be deployed"
                        },
                        "gcc_env": {
                            "type": "string",
                            "enum": ["gcc2_dev",],
                            # "enum": ["gcc2_dev", "gcc2_prd", "gccplus_stg", "gccplus_prd"],
                            "description": "The target GCC environment to deploy the feature branch to."
                        },
                        "project": {
                            "type": "string",
                            "description": "The target git project to deploy the feature branch to. For example: gcci-agency-gvt-gcc-monitoring-dev-baseline."
                        },
                    },
                    "required": ["branch", "gcc_env", "project"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "gitlab_reset_project_to_main_branch",
                "description": "This function will restore a gitlab repo from feature branch back to main branch, and trigger a pipeline for deployment. The output is the link to the deployment pipeline. Please always ask user for input if not clear, and always double confirm with user before running this function.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "The git repo feature branch that currently the project is on."
                        },
                        "gcc_env": {
                            "type": "string",
                            "enum": ["gcc2_dev", ],
                            # "enum": ["gcc2_dev", "gcc2_prd", "gccplus_stg", "gccplus_prd"],
                            "description": "The target GCC environment to deploy the feature branch to."
                        },
                        "project": {
                            "type": "string",
                            "description": "The target git project to restore to main branch. For example: gcci-agency-gvt-gcc-monitoring-dev-baseline"
                        },
                    },
                    "required": ["branch", "gcc_env", "project"],
                }
            }
        },
    ],

    "tool_functions": {
        "find_birthday": find_birthday,
        "current_datetime": current_datetime,
        "aws_find_account_details": aws_find_account_details,
        "aws_list_account_scps": aws_list_account_scps,
        "azure_find_subscription_details": azure_find_subscription_details,
        "aws_create_a_gen_vpc": aws_create_a_gen_vpc,
        "gitlab_deploy_a_feature_branch_to_project": gitlab_deploy_a_feature_branch_to_project,
        "gitlab_reset_project_to_main_branch": gitlab_reset_project_to_main_branch,
    },
}
