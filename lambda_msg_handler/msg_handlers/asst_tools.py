import logging
import os
from datetime import datetime, timezone

from msg_handlers.aws_related.utils import find_account_details, list_account_scps, create_a_gen_vpc
from msg_handlers.gitlab_related.gcc_lz_qa import deploy_a_feature_branch_to_project, reset_project_to_main_branch

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def find_birthday(**args) -> str:
    name = args['name']
    bd = "unknown"
    if "yangbo" in name.lower():
        bd = "1991.Aug"
    return bd


def current_datetime(**args) -> str:
    return datetime.now(timezone.utc).isoformat()


def aws_find_account_details(**args) -> str:
    return find_account_details(args["account_id"])


def aws_list_account_scps(**args) -> str:
    return list_account_scps(args["account_id"])


def aws_create_a_gen_vpc(**args) -> str:
    return create_a_gen_vpc(args["name"], args["cidr_block"])


def gitlab_deploy_a_feature_branch_to_project(**args) -> str:
    return deploy_a_feature_branch_to_project(args["branch"], args["project"])


def gitlab_reset_project_to_main_branch(**args) -> str:
    return reset_project_to_main_branch(args["branch"], args["project"])


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
                        }
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
                            "description": "AWS Account id."
                        }
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
                            "description": "AWS Account id."
                        }
                    },
                    "required": ["account_id"],
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
                            "description": "The network CIDR range block for the VPC."
                        }
                    }
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "gitlab_deploy_a_feature_branch_to_project",
                "description": "This function will trigger a gitlab pipeline to deploy the feature branch for the git project. The output is the link to the deployment pipeline",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "The git repo feature branch to be deployed"
                        },
                        "project": {
                            "type": "string",
                            "description": "The target git project to deploy the feature branch to"
                        }
                    }
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "gitlab_reset_project_to_main_branch",
                "description": "This function will restore a gitlab repo from feature branch back to main branch, and trigger a pipeline for deployment. The output is the link to the deployment pipeline",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "The git repo feature branch that currently the project is on."
                        },
                        "project": {
                            "type": "string",
                            "description": "The target git project to restore to main branch"
                        }
                    }
                }
            }
        },
    ],

    "tool_functions": {
        "find_birthday": find_birthday,
        "current_datetime": current_datetime,
        "aws_find_account_details": aws_find_account_details,
        "aws_list_account_scps": aws_list_account_scps,
        "aws_create_a_gen_vpc": aws_create_a_gen_vpc,
        "gitlab_deploy_a_feature_branch_to_project": gitlab_deploy_a_feature_branch_to_project,
        "gitlab_reset_project_to_main_branch": gitlab_reset_project_to_main_branch,
    },
}
