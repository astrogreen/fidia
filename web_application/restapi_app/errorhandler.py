from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render
from django.http import HttpResponse
from django.template import Context, loader


def handler404(request):
    # render to response shortcut deals with generating the context for this view
    # (template = loader.get_template(404.html)
    # "Returns a HttpResponse whose content is filled with the result of calling
    # django.template.loader.render_to_string() with the passed arguments."

    response = render_to_response('404.html', {"status_code": 404},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response
    # # 2. Generate Content for this view
    # template = loader.get_template('404.html')
    # context = Context({
    #     'message': 'All: %s' % request,
    # })
    #
    # # 3. Return Template for this view + Data
    # return HttpResponse(content=template.render(context), content_type='text/html; charset=utf-8', status=404)
