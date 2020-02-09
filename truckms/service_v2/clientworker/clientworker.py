from truckms.service.worker.worker_client import get_available_brokers
import requests
import logging
logger = logging.getLogger(__name__)
import time
import tinymongo
from truckms.service_v2.p2pdata import p2p_pull_update_one, deserialize_doc_from_net, p2p_push_update_one, p2p_insert_one
from functools import partial
import inspect
import traceback
import collections


def find_response_with_work(local_port, db, collection, func_name):

    res_broker_ip = None
    res_broker_port = None
    res_json = dict()

    brokers = get_available_brokers(local_port=local_port)

    if not brokers:
        logger.info("No broker found")

    for broker in brokers:
        broker_ip, broker_port = broker['ip'], broker['port']
        try:
            res = requests.post('http://{}:{}/search_work/{}/{}/{}'.format(broker_ip, broker_port, db, collection, func_name), timeout=5)
            if isinstance(res.json, collections.Callable): # from requests lib
                returned_json = res.json()
            else: # is property
                returned_json = res.json # from Flask test client
            if returned_json and 'filter' in returned_json:
                logger.info("Found work from {}, {}".format(broker_ip, broker_port))
                res_broker_ip = broker_ip
                res_broker_port = broker_port
                res_json = returned_json
                break
        except:  # except connection timeout or something like that
            logger.info("broker unavailable {}:{}".format(broker_ip, broker_port))
            pass

    if res_broker_ip is None:
        logger.info("No work found")

    # TODO it may be possible that res allready contains broker ip and port?
    return res_json, res_broker_ip, res_broker_port


def do_work(up_dir, db_url, local_port, func, db, collection):
    """

    """

    required_positional_args = []
    for k, v in inspect.signature(func, follow_wrapped=False).parameters.items():
        if v.default == inspect._empty:
            required_positional_args.append(v.name)
    assert all(key not in required_positional_args for key in ['identifier', 'nodes'])

    res, broker_ip, broker_port = find_response_with_work(local_port, collection, func.__name__)
    filter_ = {"identifier": res['identifier']}
    local_data = dict()
    local_data.update(filter_)
    local_data.update({k: None for k in required_positional_args})
    p2p_insert_one(db_url, db, collection, local_data, [broker_ip+":"+str(broker_port)], do_upload=False)

    deserializer = partial(deserialize_doc_from_net, up_dir=up_dir)
    # TODO instead of hardcoding here the required keys. those keys could be inspected form the function declaration,
    #  or a dectoator should be used to help the framework to know which resources the funciton needs in order to be executed on worker and workerclient.
    #  also the return value of the analysis func should be a dictionary
    #  actually the question is which function should do the pull and which function should do the push
    #  I believe that the user that implements the analysis function should have no responsability of knowing about p2p_data
    #  I will curently keep it like that, but needs refactoring
    p2p_pull_update_one(db_url, db, collection, filter_, required_positional_args, deserializer, hint_file_keys=func.hint_args_are_files)

    local_data_after_update = list(tinymongo.TinyMongoClient(db_url)[db][collection].find(filter_))[0]
    kwargs = {k: v for k, v in local_data_after_update.items() if k in required_positional_args}
    update = func(**kwargs)
    p2p_push_update_one(db_url, db, collection, filter_, update)
