# from django.test import TestCase
# from astrospark import mediator
#
# # Let's just write query related test cases here and see how it goes
#
# class QueryViewTests(TestCase):
#
#     def setUp(self):
#         # If you want to create test data, do it here
#         pass
#
#     def test_query_get_all_galaxies_in_a_pair(self):
#         # All the user input needs to be mocked up and create a query here.
#
#         pairid = 0
#         gal1_cataid = 0
#         gal2_cataid = 0
#         cataid = 0
#         z = 0
#         nq = 0
#
#         response = self.client.post('/asvo/query/', {'query': 'select all from table1'})
#         self.assertEqual(response.status_code, 302)
#
#
#     # TODO: This method should be moved elsewhere later
#     def test_querys_spark(self):
#         result = mediator.execute_query('select ra, dec from ltspecall limit 10')
#         print('query executed')
#         self.assertIsNotNone(result)
#         print(result.printSchema())
#         print(result.show())
#         mediator.stop_spark()
#         print('context stopped')