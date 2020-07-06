import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
log = logging.getLogger('cloudLogger')
log.setLevel(logging.INFO)
log.addHandler(handler)
log.error('===================+++++++++++++++++  ')
log.error('===================+++++++++++++++++  bad news')
log.error('===================+++++++++++++++++  ')


if __name__ == '__main__':
    log.info("=-=-=-=-=-=-=-=+++++ INIT =-=-=-=-=-=-=-=+++++")
    log.error("=-=-=-=-=-=-=-=+++++ ERROR =-=-=-=-=-=-=-=+++++")
    log.info("_Authenticating... v0.9.0\n")
