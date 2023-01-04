from django.core.paginator import Paginator


def split_pages(request, post_list, VIEW_ELEMENTS):
    # Показывать на странице кол-во записей = VIEW_ELEMENTS.
    paginator = Paginator(post_list, VIEW_ELEMENTS)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)

    return page_obj
