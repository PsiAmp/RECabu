import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
cloud_logger = logging.getLogger('cloudLogger')
cloud_logger.setLevel(logging.INFO) # defaults to WARN
cloud_logger.addHandler(handler)
cloud_logger.error('===================+++++++++++++++++  ')
cloud_logger.error('===================+++++++++++++++++  bad news')
cloud_logger.error('===================+++++++++++++++++  ')


if __name__ == '__main__':
    logging.info("=-=-=-=-=-=-=-=+++++ INIT =-=-=-=-=-=-=-=+++++")
    logging.error("=-=-=-=-=-=-=-=+++++ ERROR =-=-=-=-=-=-=-=+++++")
    logging.info("_Authenticating... v0.9.0\n")
