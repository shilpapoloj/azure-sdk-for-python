# coding=utf-8
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from datetime import date, time
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ClientAuthenticationError
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer._generated.models import AnalyzeOperationResult
from azure.ai.formrecognizer._response_handlers import prepare_us_receipt
from azure.ai.formrecognizer.aio import FormRecognizerClient
from testcase import GlobalFormRecognizerAccountPreparer
from asynctestcase import AsyncFormRecognizerTest


class TestReceiptFromUrlAsync(AsyncFormRecognizerTest):

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_bad_endpoint(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        with self.assertRaises(ServiceRequestError):
            client = FormRecognizerClient("http://notreal.azure.com", AzureKeyCredential(form_recognizer_account_key))
            result = await client.recognize_receipts_from_url(
                self.receipt_url_jpg
            )

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_auth_successful_key(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))
        result = await client.recognize_receipts_from_url(
            self.receipt_url_jpg
        )

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_auth_bad_key(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential("xxxx"))
        with self.assertRaises(ClientAuthenticationError):
            result = await client.recognize_receipts_from_url(
                self.receipt_url_jpg
            )

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_bad_url(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        with self.assertRaises(HttpResponseError):
            result = await client.recognize_receipts_from_url("https://badurl.jpg")

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_pass_stream(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))
        with open(self.receipt_png, "rb") as fd:
            receipt = fd.read(4)  # makes the recording smaller

        with self.assertRaises(HttpResponseError):
            result = await client.recognize_receipts_from_url(receipt)

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_transform_jpg(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        responses = []

        def callback(raw_response, _, headers):
            analyze_result = client._client._deserialize(AnalyzeOperationResult, raw_response)
            extracted_receipt = prepare_us_receipt(analyze_result)
            responses.append(analyze_result)
            responses.append(extracted_receipt)

        result = await client.recognize_receipts_from_url(
            self.receipt_url_jpg,
            include_text_content=True,
            cls=callback
        )

        raw_response = responses[0]
        returned_model = responses[1]
        receipt = returned_model[0]
        actual = raw_response.analyze_result.document_results[0].fields
        read_results = raw_response.analyze_result.read_results
        document_results = raw_response.analyze_result.document_results

        # check hardcoded values
        self.assertFormFieldTransformCorrect(receipt.merchant_address, actual.get("MerchantAddress"), read_results)
        self.assertFormFieldTransformCorrect(receipt.merchant_name, actual.get("MerchantName"), read_results)
        self.assertFormFieldTransformCorrect(receipt.merchant_phone_number, actual.get("MerchantPhoneNumber"), read_results)
        self.assertFormFieldTransformCorrect(receipt.subtotal, actual.get("Subtotal"), read_results)
        self.assertFormFieldTransformCorrect(receipt.tax, actual.get("Tax"), read_results)
        self.assertFormFieldTransformCorrect(receipt.tip, actual.get("Tip"), read_results)
        self.assertFormFieldTransformCorrect(receipt.total, actual.get("Total"), read_results)
        self.assertFormFieldTransformCorrect(receipt.transaction_date, actual.get("TransactionDate"), read_results)
        self.assertFormFieldTransformCorrect(receipt.transaction_time, actual.get("TransactionTime"), read_results)

        # check dict values
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantAddress"), actual.get("MerchantAddress"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantName"), actual.get("MerchantName"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantPhoneNumber"), actual.get("MerchantPhoneNumber"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Subtotal"), actual.get("Subtotal"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Tax"), actual.get("Tax"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Tip"), actual.get("Tip"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Total"), actual.get("Total"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("TransactionDate"), actual.get("TransactionDate"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("TransactionTime"), actual.get("TransactionTime"), read_results)

        # check page range
        self.assertEqual(receipt.page_range.first_page, document_results[0].page_range[0])
        self.assertEqual(receipt.page_range.last_page, document_results[0].page_range[1])

        # check receipt type
        self.assertEqual(receipt.receipt_type.confidence, actual["ReceiptType"].confidence)
        self.assertEqual(receipt.receipt_type.type, actual["ReceiptType"].value_string)

        # check receipt items
        self.assertReceiptItemsTransformCorrect(receipt.receipt_items, actual["Items"], read_results)

        # Check page metadata
        self.assertFormPagesTransformCorrect(receipt.pages, read_results)

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_transform_png(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        responses = []

        def callback(raw_response, _, headers):
            analyze_result = client._client._deserialize(AnalyzeOperationResult, raw_response)
            extracted_receipt = prepare_us_receipt(analyze_result)
            responses.append(analyze_result)
            responses.append(extracted_receipt)

        result = await client.recognize_receipts_from_url(
            self.receipt_url_png,
            include_text_content=True,
            cls=callback
        )

        raw_response = responses[0]
        returned_model = responses[1]
        receipt = returned_model[0]
        actual = raw_response.analyze_result.document_results[0].fields
        read_results = raw_response.analyze_result.read_results
        document_results = raw_response.analyze_result.document_results

        # check hardcoded values
        self.assertFormFieldTransformCorrect(receipt.merchant_address, actual.get("MerchantAddress"), read_results)
        self.assertFormFieldTransformCorrect(receipt.merchant_name, actual.get("MerchantName"), read_results)
        self.assertFormFieldTransformCorrect(receipt.merchant_phone_number, actual.get("MerchantPhoneNumber"), read_results)
        self.assertFormFieldTransformCorrect(receipt.subtotal, actual.get("Subtotal"), read_results)
        self.assertFormFieldTransformCorrect(receipt.tax, actual.get("Tax"), read_results)
        self.assertFormFieldTransformCorrect(receipt.tip, actual.get("Tip"), read_results)
        self.assertFormFieldTransformCorrect(receipt.total, actual.get("Total"), read_results)
        self.assertFormFieldTransformCorrect(receipt.transaction_date, actual.get("TransactionDate"), read_results)
        self.assertFormFieldTransformCorrect(receipt.transaction_time, actual.get("TransactionTime"), read_results)

        # check dict values
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantAddress"), actual.get("MerchantAddress"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantName"), actual.get("MerchantName"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("MerchantPhoneNumber"), actual.get("MerchantPhoneNumber"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Subtotal"), actual.get("Subtotal"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Tax"), actual.get("Tax"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Tip"), actual.get("Tip"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("Total"), actual.get("Total"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("TransactionDate"), actual.get("TransactionDate"), read_results)
        self.assertFormFieldTransformCorrect(receipt.fields.get("TransactionTime"), actual.get("TransactionTime"), read_results)

        # check page range
        self.assertEqual(receipt.page_range.first_page, document_results[0].page_range[0])
        self.assertEqual(receipt.page_range.last_page, document_results[0].page_range[1])

        # check receipt type
        self.assertEqual(receipt.receipt_type.confidence, actual["ReceiptType"].confidence)
        self.assertEqual(receipt.receipt_type.type, actual["ReceiptType"].value_string)

        # check receipt items
        self.assertReceiptItemsTransformCorrect(receipt.receipt_items, actual["Items"], read_results)

        # Check page metadata
        self.assertFormPagesTransformCorrect(receipt.pages, read_results)

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_include_text_content(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        result = await client.recognize_receipts_from_url(
            self.receipt_url_jpg,
            include_text_content=True
        )

        self.assertEqual(len(result), 1)
        receipt = result[0]

        self.assertFormPagesHasValues(receipt.pages)
        for field, value in receipt.__dict__.items():
            if field not in ["receipt_type", "receipt_items", "page_range", "pages", "fields", "form_type", "receipt_locale"]:
                field = getattr(receipt, field)
                self.assertTextContentHasValues(field.value_data.text_content, receipt.page_range.first_page)

        for field, value in receipt.fields.items():
            self.assertTextContentHasValues(value.value_data.text_content, receipt.page_range.first_page)

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_jpg(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        result = await client.recognize_receipts_from_url(
            self.receipt_url_jpg
        )

        self.assertEqual(len(result), 1)
        receipt = result[0]
        self.assertEqual(receipt.merchant_address.value, '123 Main Street Redmond, WA 98052')
        self.assertEqual(receipt.merchant_name.value, 'Contoso Contoso')
        self.assertEqual(receipt.merchant_phone_number.value, '+19876543210')
        self.assertEqual(receipt.subtotal.value, 11.7)
        self.assertEqual(receipt.tax.value, 1.17)
        self.assertEqual(receipt.tip.value, 1.63)
        self.assertEqual(receipt.total.value, 14.5)
        self.assertEqual(receipt.transaction_date.value, date(year=2019, month=6, day=10))
        self.assertEqual(receipt.transaction_time.value, time(hour=13, minute=59, second=0))
        self.assertEqual(receipt.page_range.first_page, 1)
        self.assertEqual(receipt.page_range.last_page, 1)
        self.assertFormPagesHasValues(receipt.pages)
        self.assertIsNotNone(receipt.receipt_type.confidence)
        self.assertEqual(receipt.receipt_type.type, 'Itemized')
        self.assertReceiptItemsHasValues(receipt.receipt_items, receipt.page_range.first_page, False)

    @GlobalFormRecognizerAccountPreparer()
    async def test_receipt_url_png(self, resource_group, location, form_recognizer_account, form_recognizer_account_key):
        client = FormRecognizerClient(form_recognizer_account, AzureKeyCredential(form_recognizer_account_key))

        result = await client.recognize_receipts_from_url(self.receipt_url_png)

        self.assertEqual(len(result), 1)
        receipt = result[0]
        self.assertEqual(receipt.merchant_address.value, '123 Main Street Redmond, WA 98052')
        self.assertEqual(receipt.merchant_name.value, 'Contoso Contoso')
        self.assertEqual(receipt.subtotal.value, 1098.99)
        self.assertEqual(receipt.tax.value, 104.4)
        self.assertEqual(receipt.total.value, 1203.39)
        self.assertEqual(receipt.transaction_date.value, date(year=2019, month=6, day=10))
        self.assertEqual(receipt.transaction_time.value, time(hour=13, minute=59, second=0))
        self.assertEqual(receipt.page_range.first_page, 1)
        self.assertEqual(receipt.page_range.last_page, 1)
        self.assertFormPagesHasValues(receipt.pages)
        self.assertIsNotNone(receipt.receipt_type.confidence)
        self.assertEqual(receipt.receipt_type.type, 'Itemized')