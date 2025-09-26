from typing import Any

from fastapi.requests import Request

from goosebit.ui.bff.common.requests import DataTableRequest


def parse_datatables_query(request: Request) -> DataTableRequest:
    # parsing adapted from https://github.com/ziiiio/datatable_ajax_request_parser

    result: dict[str, Any] = {}
    for key, value in request.query_params.items():
        key_list = key.replace("][", ";").replace("[", ";").replace("]", "").split(";")

        if len(key_list) == 0:
            continue

        if len(key_list) == 1:
            result[key] = value[0] if len(value) == 1 else value
            continue

        temp_dict: dict[str, Any] = result
        for inner_key in key_list[:-1]:
            if inner_key not in temp_dict:
                temp_dict.update({inner_key: {}})
            temp_dict = temp_dict[inner_key]
        temp_dict[key_list[-1]] = value[0] if len(value) == 1 else value

    if result.get("columns"):
        columns_dict = result["columns"]
        result["columns"] = [columns_dict[str(idx)] for idx, _ in enumerate(columns_dict)]
    if result.get("order"):
        order_dict = result["order"]
        result["order"] = [order_dict[str(idx)] for idx, _ in enumerate(order_dict)]

    return DataTableRequest.model_validate(result)
