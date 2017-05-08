from rest_framework_csv import renderers as r


class MyCSVQueryRenderer(r.CSVRenderer):
    """
    Return only the results field rather than the full query model instance.
    """
    results_field = 'results'

    def render(self, data, accepted_media_type=None, renderer_context=None):

        if not isinstance(data, list):
            # data must be a list of dicts, where the keys are the headers
            # data = [{"a": '1', "b": '2'}, {"a": "3", "b": "4"}]

            # get the results field from the model instance
            results = data.get(self.results_field, [])

            headers = []
            data = []

            if "columns" in results:
                # headers are in the column property
                headers = list(map(lambda x: x["name"], results["columns"]))

            if "data" in results:
                for row in results["data"]:
                    data.append(dict(zip(headers, row)))

        return super(MyCSVQueryRenderer, self).render(data, accepted_media_type, renderer_context)
