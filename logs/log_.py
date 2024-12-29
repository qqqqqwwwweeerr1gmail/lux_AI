import logging

def g_l(game_id):
    # Configure logging
    logging.basicConfig(filename='./logs/lux_'+game_id+'.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a logger
    l = logging.getLogger(__name__)
    return l



if __name__ == '__main__':
    l = g_l('aaa')
    # Log messages at different levels
    l.debug('This is a debug message')
    l.info('This is an informational message')
    l.warning('This is a warning message')
    l.error('This is an error message')
    l.critical('This is a critical message')
    # Log an exception
    try:
        10 / 0
    except ZeroDivisionError as e:
        l.exception("An error occurred:", exc_info=True)
























