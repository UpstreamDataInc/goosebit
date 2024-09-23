from fastapi.requests import Request

from goosebit.ui.bff.common.requests import DataTableRequest


def parse_datatables_query(request: Request):
    # parsing adapted from https://github.com/ziiiio/datatable_ajax_request_parser

    result = {}
    for key, value in request.query_params.items():
        key_list = key.replace("][", ";").replace("[", ";").replace("]", "").split(";")

        if len(key_list) == 0:
            continue

        if len(key_list) == 1:
            result[key] = value[0] if len(value) == 1 else value
            continue

        temp_dict = result
        for inner_key in key_list[:-1]:
            if inner_key not in temp_dict:
                temp_dict.update({inner_key: {}})
            temp_dict = temp_dict[inner_key]
        temp_dict[key_list[-1]] = value[0] if len(value) == 1 else value

    if result.get("columns"):
        result["columns"] = [result["columns"][str(idx)] for idx, _ in enumerate(result["columns"])]
    if result.get("order"):
        result["order"] = [result["order"][str(idx)] for idx, _ in enumerate(result["order"])]

    return DataTableRequest.model_validate(result)
