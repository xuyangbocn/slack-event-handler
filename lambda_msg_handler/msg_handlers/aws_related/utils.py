import logging
import json
import boto3
import botocore
from boto3.dynamodb.types import TypeDeserializer

sts_client = boto3.client('sts')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_sts_client(service, role_arn):
    """
    Get sts assume role credential to call boto3 APIs when assuming cross-account roles.
    Args:
        service: the service name used for calling the boto.client()
        role_arn: the ARN of the role to assume
    Return:
        service boto3 client. 
    """
    resp = sts_client.assume_role(
        RoleArn=role_arn, RoleSessionName=f"SlackApp_Assume_role_for_{service}")
    credentials = resp['Credentials']

    return boto3.client(service, aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken']
                        )


def find_account_details(iam_role_arn, account_id) -> str:
    '''
    args:
        iam_role_arn (str): iam role to assume
        account_id (str): 12 digit account id 
    '''
    try:
        org = get_sts_client('organizations', iam_role_arn)
        response = org.describe_account(
            AccountId=account_id
        )
        ret = str(response['Account'])
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccountNotFoundException':
            ret = f"account id {account_id} not found"
        else:
            ret = f"Fail to search aws account, due to error {str(error)}"

    return ret


def find_subscription_details(iam_role_arn, subscription_id) -> str:
    '''
    Query CloudResourceDetails table in Core-shared-service
    args:
        iam_role_arn (str): iam role to assume
        subscription_id (str): alphanumeric with hyphen, total 36 characters
    '''
    d = TypeDeserializer()
    try:
        ddb = get_sts_client('dynamodb', iam_role_arn)
        resp = ddb.query(
            TableName='CloudResourceDetails',
            IndexName='ResourceParentIndex',
            KeyConditionExpression='#rt_rid = :rt_rid',
            ExpressionAttributeValues={
                ':rt_rid': {
                    'S': f'CSPAcc/{subscription_id}',
                }
            },
            ExpressionAttributeNames={
                "#rt_rid": "ResourceType#ResourceId"
            }
        )
        record = {
            k: d.deserialize(value=v) for k, v in
            resp.get('Items')[0]['Details']['M'].items()
        }
        record.pop('AccountName', '')
        record.pop('AccountId', '')
        record.pop('AccountType', '')
        record.pop('Provider', '')
        git = json.loads(record.pop('GitLabDetails', '{}'))
        # record['Gitlab Repo'] = git.get('WebUrl')
        # record['Gitlab Repo Path'] = git.get('PathWithNamespace')
        record['Subscription Id'] = subscription_id
        ret = json.dumps(record, indent=2)
    except (botocore.exceptions.ClientError, KeyError) as exNotFound:
        ret = f"Subscription {subscription_id} not found"

    return ret


def list_account_scps(iam_role_arn, account_id) -> str:
    '''
    args:
        iam_role_arn (str): iam role to assume
        account_id (str): 12 digit account id 
    '''
    target_id = account_id
    target_type = ""
    ret = ""
    while target_type != "ROOT":
        try:
            org = get_sts_client('organizations', iam_role_arn)
            policies = org.list_policies_for_target(
                TargetId=target_id,
                Filter='SERVICE_CONTROL_POLICY',
            )
            ret += ", ".join([p['Name'] for p in policies['Policies']])

            parent_target = org.list_parents(
                ChildId=target_id,
            )
            target_id = parent_target["Parents"][0]["Id"]
            target_type = parent_target["Parents"][0]["Type"]
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] in ('TargetNotFoundException', 'ChildNotFoundException'):
                ret = f"account id {account_id} not found"
            else:
                ret = f"Fail to search aws account, due to error {str(error)}"
            break

    return ret


def create_a_gen_vpc(iam_role_arn, name, cidr_block) -> str:
    '''
    args:
        iam_role_arn (str): iam role to assume
        name (str): vpc tag for name
        cidr_block (str): cidr_block for VPC creation
    '''
    try:
        ec2 = get_sts_client('ec2', iam_role_arn)
        response = ec2.create_vpc(
            CidrBlock=cidr_block,
            AmazonProvidedIpv6CidrBlock=False,
            DryRun=False,
            InstanceTenancy='default',
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name
                        }, {
                            'Key': 'CompartmentType',
                            'Value': "GEN"
                        }
                    ]
                },
            ]
        )
        ret = f"VPC created successfully, vpc id is {response['Vpc']['VpcId']}"
    except botocore.exceptions.ClientError as error:
        ret = f"Fail to create vpc, due to error {str(error)}"

    return ret
