from background_task import background
import datetime
from fcm.models import *

from api.models import RestaurantInfo, Order
from django.http import JsonResponse


def my_response(status, message, data):
    return JsonResponse({
        'status': status,
        'message': message,
        'data': data,
    })


def image_name():
    name = datetime.datetime.now()
    name = str(name).replace(' ', '_')
    name = name.split('.')[0].replace(':', '-')

    return name


def merge(foods, options, fav_op, fav_fo):
    result = []
    i = j = 0
    total = len(foods) + len(options)
    while len(result) != total:
        if len(foods) == i:
            while j < len(options):
                if options[j].option_id in fav_op and options[j].status:
                    result.append(options[j].to_json(fav=True, with_group=True))
                else:
                    result.append(options[j].to_json(with_group=True))
                j += 1
            # result += options[j:]
            break
        elif len(options) == j:
            while i < len(foods):
                if foods[i].food_id in fav_fo and foods[i].status:
                    result.append(foods[i].to_json(fav=True, with_group=True))
                else:
                    result.append(foods[i].to_json(with_group=True))
                i += 1
            # result += foods[i:]
            break
        elif foods[i].rank > options[j].rank:
            if foods[i].food_id in fav_fo and foods[i].status:
                result.append(foods[i].to_json(fav=True, with_group=True))
            else:
                result.append(foods[i].to_json(with_group=True))
            i += 1
        else:
            if options[j].option_id in fav_op and options[j].status:
                result.append(options[j].to_json(fav=True, with_group=True))
            else:
                result.append(options[j].to_json(with_group=True))
            j += 1
    return result


def get_hour_minute():
    return datetime.datetime.now().time().strftime('%H:%M')


def is_between(time, time_range):
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]


def time_diff(time1, time2):
    time_a = datetime.datetime.strptime(time1, "%H:%M")
    time_b = datetime.datetime.strptime(time2, "%H:%M")
    new_time = time_a - time_b
    return new_time.seconds / 60


def check_allow_record_order(now_time):
    res = RestaurantInfo.objects.first()
    ts = res.time_slot
    created_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=ts)
    count_before_order = Order.objects.filter(datetime__range=(created_time, now_time)).count()
    max_order = res.max_order_per_time_slot
    if count_before_order <= max_order:
        return True
    return False


@background(schedule=10, queue='my-queue')
def notif_to_admin_in_background(**kwargs):
    admins_notif = Device.objects.filter(name='appAdmin')
    data = {
        'orderId': kwargs['orderId'],
        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
    }
    notif = {
        'title': kwargs['title'],
        'body': kwargs['message'],
        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
        "sound": "default",
    }

    for an in admins_notif:
        an.send_message(
            data,
            notification=notif,
        )


def notif_to_admin(**kwargs):
    admins_notif = Device.objects.filter(name='appAdmin')
    data = {
        'orderId': kwargs['orderId'],
        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
    }
    notif = {
        'title': kwargs['title'],
        'body': kwargs['message'],
        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
        "sound": "default",
    }

    for an in admins_notif:
        an.send_message(
            data,
            notification=notif,
        )
