from hyperion import logging
print(id(logging.stream_handler))
#logging.set_stream(compact=1)
#print(id(logging.stream_handler))

logger = logging.getLogger(__name__)
logger.info('info')