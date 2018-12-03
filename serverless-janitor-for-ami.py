import datetime, boto3, os, json, logging
from botocore.exceptions import ClientError
import datetime, sys


# Set the global variables
globalVars  = {}
globalVars['Owner']                 = "Miztiik"
globalVars['Environment']           = "Development"
globalVars['REGION_NAME']           = "eu-central-l"
globalVars['tagName']               = "Serverless-AMI-CleanUp-Bot"
globalVars['findNeedle']            = "DeleteOn"
globalVars['RetentionDays']         = "30"
globalVars['tagsToExclude']         = "Do-Not-Delete"

ec2_client = boto3.client('ec2')

# Set the log format - Too many lines, need to sort this
logger = logging.getLogger()
for h in logger.handlers:
  logger.removeHandler(h)

h = logging.StreamHandler(sys.stdout)
FORMAT = ' [%(levelname)s]/%(asctime)s/%(name)s - %(message)s'
h.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(h)
logger.setLevel(logging.INFO)


"""
If User provides different values, override defaults
"""
def setGlobalVars():
    try:
        if os.environ['findNeedle']:
            globalVars['findNeedle']  = os.environ['findNeedle']
    except KeyError as e:
        logger.error("User Customization Environment variables are not set")
        logger.error('ERROR: {0}'.format( str(e) ) )

    try:        
        if os.environ['RetentionDays']:
            globalVars['RetentionDays'] = os.environ['RetentionDays']
    except KeyError as e:
        logger.error("User Customization Environment variables are not set")
        logger.error('ERROR: {0}'.format( str(e) ) )
        
    try:        
        if os.environ['tagsToExclude']:
            globalVars['tagsToExclude']  = os.environ['tagsToExclude']
    except KeyError as e:
        logger.error("User Customization Environment variables are not set")
        logger.error('ERROR: {0}'.format( str(e) ) )

"""
This function looks at *all* AMIs that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. This function should be run at least
daily.
"""

def janitor_for_ami():
    account_ids = list()
    account_ids.append( boto3.client('sts').get_caller_identity().get('Account') )

    ami_older_than_RetentionDays = ( datetime.date.today() - datetime.timedelta(days= int(globalVars['RetentionDays'])) ).strftime('%Y-%m-%d')
    delete_today = datetime.date.today().strftime('%Y-%m-%d')

    # Filter for instances having the needle tag
    FILTER_1 = {'Name': 'tag:' + globalVars['findNeedle'],  'Values': [delete_today]}

    # Get list of AMIs with Tag 'globalVars['findNeedle']'
    amis_to_remove = ec2_client.describe_images( Owners = account_ids, Filters = [ FILTER_1 ] )

    logger.info("Number of AMI to delete = {0}".format( len(amis_to_remove['Images']) ) )
    # Lets start prepare the function return data-dict/json
    amisDeleted = {'Images': [], 'ImgRemovalFailures':[], 'AMIs-Deleted':''}
    amisDeleted['Total-AMI-Found'] = len(amis_to_remove['Images'])

    for ami in amis_to_remove['Images']:

        # Get the instance ID tag, if it was set
        OriginalInstanceID = ''
        for tag in ami['Tags']:
            if tag['Key'] == 'OriginalInstanceID' :
                OriginalInstanceID = tag['Value']
        try:
            ec2_client.deregister_image(ImageId=ami['ImageId'])
        except ClientError as e:
            logger.error('ERROR: Not able to delete AMI. {0}'.format( str(e) ) )
            amisDeleted['ImgRemovalFailures'].append( {'Description': str(e), 'ImageId': ami['ImageId'] } )
            return amisDeleted

        for dev in ami['BlockDeviceMappings']:
            try:
                if 'Ebs' in dev:
                    ec2_client.delete_snapshot( SnapshotId = dev['Ebs']['SnapshotId'] )
                    logger.info('Deleted snapshot {0}'.format( dev['Ebs']['SnapshotId'] ) )
            except ClientError as e:
                logger.error('ERROR: Not able to delete Snapshot. {0}'.format( str(e) ) )
                pass

        logger.info('Deregistered AMI = {0}'.format( ami['ImageId'] ) )
        amisDeleted['Images'].append({'ImageId': ami['ImageId'], 'OriginalInstanceID': OriginalInstanceID, 'AMI-Name': ami['Name'], 'OwnerId': ami['OwnerId']})

    amisDeleted['AMIs-Deleted']= len(amisDeleted['Images'])

    return amisDeleted

def lambda_handler(event, context):
    setGlobalVars()
    return janitor_for_ami()

if __name__ == '__main__':
    lambda_handler(None, None)

