import json
import time
from datetime import datetime
from bravado.exception import HTTPError, HTTPTooManyRequests, HTTPServiceUnavailable

from database.LogService import LogService
from enums.ApiStage import ApiStage
from enums.OrderStatus import OrderStatus
from enums.OrderSide import OrderSide
from enums.PositionType import PositionType
from exceptions import IllegalActionException
from market_apis.BitmexClientFactory import get_bitmex_api_client
from models.ApiCallLog import LOG_MESSAGE_LENGTH
from models.Order import Order
from models.Position import Position
from utils.json_utils import to_json
from utils.TimeUtils import get_past_utc_date
from models.AlgorithmStepSnapshot import AlgorithmStepSnapshot
from models.AlgorithmRun import AlgorithmRun

GET_ORDERS_COUNT = 500
COUNT_DEFAULT = 1000
BIN_SIZE_DEFAULT = '1m'
BITCOIN_SYMBOL = 'XBTUSD'

MAX_RETRY_COUNT = 100
DURATION_BETWEEN_RETRIES = 2


class BitmexAPI:

    def __init__(self, api_stage: ApiStage, caller, session=None, with_verbose_logging=False):
        self.__bitmex_client = self.init_bitmex_client(api_stage)
        self.__log_service = LogService(session)
        self.__api_vendor_name = 'Bitmex' + api_stage.value
        self.__caller = caller
        self.__with_verbose_logging = with_verbose_logging

    def init_bitmex_client(self, api_stage):
        time_of_call = datetime.now()

        try:
            return get_bitmex_api_client(api_stage)
        except HTTPError as e:
            status_code = ''
            error_message = ''
            print('Response Code = ', status_code)
            print()
            print('Error Message = ', error_message)

            self.__log_service.log_api_call(vendor=self.__api_vendor_name,
                                            api_name='INITIALISATION_OF_BITMEX_CLIENT',
                                            status_code=status_code,
                                            error_message=error_message,
                                            response_body='',
                                            time_of_call=time_of_call,
                                            caller=self.__caller)
            raise e

    def get_current_btc_price(self):
        last_trade = self.get_last_n_trades(symbol='XBTUSD', n=1)[0]
        return last_trade['price']

    def get_bucketed_trades(self, symbol=BITCOIN_SYMBOL, bin_size=BIN_SIZE_DEFAULT, n=COUNT_DEFAULT, reverse=True):
        def get_last_bucketed_trades_api_call():
            result = self.__bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=bin_size, count=n,
                                                                  reverse=reverse).result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_LAST_{}_{}_BUCKETED_TRADES_FOR_{}'.format(n, bin_size, symbol),
                                   api_call=get_last_bucketed_trades_api_call)

    def get_bucketed_trades_since_timestamp(self, timestamp, symbol=BITCOIN_SYMBOL, bin_size=BIN_SIZE_DEFAULT,
                                            max_result_count=COUNT_DEFAULT):
        def get_bucketed_trades_since_timestamp_api_call():
            result = self.__bitmex_client.Trade.Trade_getBucketed(symbol=symbol, startTime=timestamp, binSize=bin_size,
                                                                  count=max_result_count).result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(
            api_name='GET_{}_BUCKETED_TRADES_SINCE_{}_FOR_{}_MAX_{}'.format(bin_size, timestamp, symbol,
                                                                            max_result_count),
            api_call=get_bucketed_trades_since_timestamp_api_call)

    def place_order(self, order: Order):
        def place_order_api_call():
            size_sign = 1 if order.order_side == OrderSide.BUY else -1

            result = self.__bitmex_client.Order.Order_new(symbol='XBTUSD',
                                                          orderQty=size_sign * order.size,
                                                          price=order.price,
                                                          clOrdID=order.reference_key,
                                                          ordType='Limit').result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='PLACE_ORDER_{}'.format(order.reference_key), api_call=place_order_api_call)

    def add_stop_loss(self, order: Order):
        def add_stop_loss_api_call():
            result = self.__bitmex_client.Order.Order_new(symbol='XBTUSD',
                                                          side=order.order_side.value,
                                                          clOrdID=order.reference_key,
                                                          ordType='Stop',
                                                          stopPx=order.price,
                                                          execInst='LastPrice,Close').result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='ADD_STOP_LOSS_{}'.format(order.reference_key),
                                   api_call=add_stop_loss_api_call)

    def cancel_order_by_ref_key(self, ref_key: str):
        def cancel_order_api_call():
            result = self.__bitmex_client.Order.Order_cancel(clOrdID=ref_key).result()

            status_code = str(result[1])
            response_body = to_json(result[0][0])
            result_object = result[0][0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='CANCEL_ORDER_{}'.format(ref_key), api_call=cancel_order_api_call)

    def execute_order_on_market(self, order):
        def execute_order_api_call():
            size_sign = 1 if order.order_side == OrderSide.BUY else -1

            result = self.__bitmex_client.Order.Order_new(symbol='XBTUSD',
                                                          orderQty=size_sign * order.size,
                                                          clOrdID=order.reference_key,
                                                          ordType='Market').result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='EXECUTE_ORDER_{}'.format(order.reference_key),
                                   api_call=execute_order_api_call)

    def get_position(self) -> Position:
        def extract_position_from_response(response):
            qty = response['currentQty']
            size = abs(qty)
            price = response['avgEntryPrice']
            position_type = PositionType.LONG if qty >= 0 else PositionType.SHORT

            return Position(size=size, price=price, position_type=position_type)

        def get_position_api_call():
            result = self.__bitmex_client.Position.Position_get().result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = extract_position_from_response(result[0][0])

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_POSITION', api_call=get_position_api_call)

    def get_last_n_trades(self, symbol, n):
        def get_trades_api_call():
            result = self.__bitmex_client.Trade.Trade_get(symbol=symbol, count=n, reverse=True).result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_LAST_{}_TRADES_FOR_{}'.format(n, symbol), api_call=get_trades_api_call)

    def get_btc_balance(self):
        def get_btc_balance_api_call():
            result = self.__bitmex_client.User.User_getMargin(currency='XBt').result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]['walletBalance'] * 0.00000001

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_BTC_BALANCE', api_call=get_btc_balance_api_call)

    def get_order_executions_in_last_n_minutes(self, n=None):
        start_time = get_past_utc_date(seconds=60 * n) if n is not None else None

        def get_order_executions_api_call():
            result = self.__bitmex_client.Execution.Execution_get(startTime=start_time).result()
            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_ORDER_EXECUTIONS_IN_LAST_{}_MINUTES'.format(n),
                                   api_call=get_order_executions_api_call)

    def get_orders_of_given_status_in_last_n_minutes(self, order_status: OrderStatus = None, n=None):

        def get_orders_api_call():
            def get_filter_object():
                if order_status is None:
                    return None
                elif order_status == OrderStatus.EXECUTED:
                    return json.dumps({
                        'ordStatus': 'Filled'
                    })
                elif order_status == OrderStatus.CANCELED:
                    return json.dumps({
                        'ordStatus': 'Canceled'
                    })
                elif order_status == OrderStatus.PLACED:
                    return json.dumps({
                        'open': True
                    })
                else:
                    error_message = '''
Trying to perform an API call to Bitmex API with order_status = {}. This order status is unknown
                    '''.format(order_status)
                    raise IllegalActionException(error_message)

            filter_object = get_filter_object()
            start_time = get_past_utc_date(seconds=60 * n) if n is not None else None
            print('Getting Orders of status {} between {} and {}'.format(str(order_status), start_time, get_past_utc_date(0)))
            result = self.__bitmex_client.Order.Order_getOrders(count=GET_ORDERS_COUNT, reverse=True,
                                                                filter=filter_object, startTime=start_time).result()

            status_code = str(result[1])
            response_body = to_json(result[0])
            result_object = result[0]

            return status_code, response_body, result_object

        return self.__run_with_log(api_name='GET_{}_ORDERS_IN_LAST_{}_MINUTES'.format(str(order_status), n),
                                   api_call=get_orders_api_call)

    def __run_with_log(self, api_name, api_call, retry_count=0):
        time_of_call = datetime.now()
        status_code = ''
        error_message = ''
        concatenated_response_body = ''
        full_response_body = ''

        try:
            (status_code, response_message, result_object) = api_call()

            status_code = status_code
            full_response_body = response_message
            concatenated_response_body = response_message[:LOG_MESSAGE_LENGTH]

            return result_object

        except (HTTPTooManyRequests, HTTPServiceUnavailable) as e:
            status_code = str(e.response)
            error_message = str(e)[:LOG_MESSAGE_LENGTH]
            print('STATUS CODE: ', status_code)
            print('ERROR: ', error_message)
            if retry_count <= MAX_RETRY_COUNT:
                print('retry_count ({}) <= max_retry_count({})'.format(retry_count, MAX_RETRY_COUNT))
                print('-> Sleeping for {} seconds and retrying'.format(DURATION_BETWEEN_RETRIES))
                time.sleep(DURATION_BETWEEN_RETRIES)
                return self.__run_with_log(api_name=api_name, api_call=api_call, retry_count=retry_count + 1)
            else:
                print('retry_count ({}) > max_retry_count({})'.format(retry_count, MAX_RETRY_COUNT))
                print('-> Throwing an error')
                status_code = str(e.response)
                error_message = str(e)[:LOG_MESSAGE_LENGTH]

                raise e


        except HTTPError as e:
            status_code = str(e.response)
            error_message = str(e)[:LOG_MESSAGE_LENGTH]

            raise e
        finally:
            print('-------------------------------------API CALL BEGINNING----------------------------')
            print('API Name = ', api_name)
            print('Response Code = ', status_code)
            print('Api Executed at = ', time_of_call)

            if self.__with_verbose_logging:
                print()
                print('Full Response Body = ', full_response_body)
                print()
                print('Error Message = ', error_message)
            print('-------------------------------------API CALL END---------------------------------')

            self.__log_service.log_api_call(vendor=self.__api_vendor_name,
                                            api_name=api_name,
                                            status_code=status_code,
                                            error_message=error_message,
                                            response_body=concatenated_response_body,
                                            time_of_call=time_of_call,
                                            caller=self.__caller)
