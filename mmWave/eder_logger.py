import logging

class EderLogger(object):

    import readline

    __instance = None

    def __new__(cls, fname='eder.info'):
        if cls.__instance is None:
            cls.__instance = super(EderLogger, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, fname='eder.info'):
        if self.__initialized:
            return
        self._last_hist_item_idx = self.readline.get_current_history_length()
        self._logger = logging.getLogger('eder_logger')
        self._logger.setLevel(logging.DEBUG)
        self._fh = logging.FileHandler(fname)
        self._fh.setLevel(logging.DEBUG)
        self._ch = logging.StreamHandler()
        self._ch.setLevel(logging.INFO)
        file_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        scr_format = logging.Formatter('%(message)s')
        self._ch.setFormatter(scr_format)
        self._fh.setFormatter(file_format)
        self._logger.addHandler(self._ch)
        self._logger.addHandler(self._fh)
        self.__initialized = True

    def log_info(self, message, indentation=0):
        self._log_cmd_hist() 
        self._logger.info(' '*indentation + str(message))

    def log_warning(self, message, indentation=0):
        self._log_cmd_hist()
        self._logger.warning(' '*indentation + str(message))

    def log_debug(self, message, indentation=0):
        self._log_cmd_hist()
        self._logger.debug(' '*indentation + str(message))

    def log_error(self, message, indentation=0):
        self._log_cmd_hist()
        self._logger.error(' '*indentation + str(message))

    def log_critical(self, message, indentation=0):
        self._log_cmd_hist()
        self._logger.critical(' '*indentation + str(message))

    def _log_cmd_hist(self):
        current_hist_length = self.readline.get_current_history_length()
        if current_hist_length > self._last_hist_item_idx:
            for index in xrange(self._last_hist_item_idx, current_hist_length+1):
                self._logger.debug(self.readline.get_history_item(index))
        self._last_hist_item_idx = current_hist_length

