import boto3
import botocore

org = boto3.client(
    'organizations',
    aws_access_key_id="ACCESS_KEY",
    aws_secret_access_key="SECRET_KEY",
    aws_session_token="SESSION_TOKEN"
)
ec2 = boto3.client(
    'ec2',
    aws_access_key_id="ACCESS_KEY",
    aws_secret_access_key="SECRET_KEY",
    aws_session_token="SESSION_TOKEN"
)


def find_account_details(account_id) -> str:
    '''
    args:
        account_id (str): 12 digit account id 
    '''
    try:
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


def list_account_scps(account_id) -> str:
    '''
    args:
        account_id (str): 12 digit account id 
    '''
    target_id = account_id
    target_type = ""
    ret = ""
    while target_type != "ROOT":
        try:
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


def create_a_gen_vpc(name, cidr_block) -> str:
    '''
    args:
        name (str): vpc tag for name
        cidr_block (str): cidr_block for VPC creation
    '''
    try:
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
