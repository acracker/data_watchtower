#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import APIRouter, status

router = APIRouter()

# @router.post(
#     "/endpoints",
#     response_model=DefaultResponseModel,  # default response pydantic model
#     status_code=status.HTTP_201_CREATED,  # default status code
#     description="Description of the well documented endpoint",
#     tags=["Endpoint Category"],
#     summary="Summary of the Endpoint",
#     responses={
#         status.HTTP_200_OK: {
#             "model": OkResponse, # custom pydantic model for 200 response
#             "description": "Ok Response",
#         },
#         status.HTTP_201_CREATED: {
#             "model": CreatedResponse,  # custom pydantic model for 201 response
#             "description": "Creates something from user request ",
#         },
#         status.HTTP_202_ACCEPTED: {
#             "model": AcceptedResponse,  # custom pydantic model for 202 response
#             "description": "Accepts request and handles it later",
#         },
#     },
# )