from celery import signals, states
from elasticapm import set_transaction_outcome
from elasticapm.conf import constants
from elasticapm.utils import get_name_from_func


def register_dcu_transaction_handler(client):
    def end_transaction(task_id, task, *args, **kwargs):
        if task.name:
            name = task.name
        else:
            name = get_name_from_func(task)
        name = get_name_from_func(task)
        state = kwargs.get("state", "None")
        if state == states.SUCCESS:
            outcome = constants.OUTCOME.SUCCESS
        elif state in states.EXCEPTION_STATES:
            outcome = constants.OUTCOME.FAILURE
        else:
            outcome = constants.OUTCOME.UNKNOWN
        set_transaction_outcome(outcome, override=False)
        client.end_transaction(name, state)

    dispatch_uid = "elasticapm-tracing-%s"
    signals.task_postrun.disconnect(end_transaction, dispatch_uid=dispatch_uid % "postrun")
    signals.task_postrun.connect(end_transaction, weak=False, dispatch_uid=dispatch_uid % "postrun")
