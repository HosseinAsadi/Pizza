import random
from json import loads
import hashlib

from api import admin
from api.for_email import send_email
from api.models import User, Group, Food, FoodSize, Token, Favorite, Option, Address, \
    OrderOption, RestaurantTime, OrderFood, FoodOption, FoodType, RestaurantAddress, Ticket, Otp, \
    Payment, OrderType, OptionType
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from api.pay import *
from api.utils import *


@csrf_exempt
def base(request):
    # Device.objects.filter(name='appAdmin').delete()
    # Device(name='test',
    #        reg_id='eWx07pYiQTSrItcVoHh3yb:APA91bG2IMOuoF0b0V1oFyVskK5R6G1CgsNKSr2jNPiNbeILRIsW14qYTvAKdvDJ6UWU93kAzyhB_-LBfBW5TojTcS47Gbx34wRcuZ31xfAyifwubUWELnfk2qEVQikfS5vczm2b1AVw',
    #        dev_id='6097c81d1b183c55', is_active=True).save()

    # print(Device.objects.get(name='test').send_message({'ss':"ss"}))
    return HttpResponse(content='<p1>this is server api for pizza project</p1>')


@csrf_exempt
def register(request):
    if request.method == "POST":
        try:
            info = loads(request.body.decode('utf-8'))

            p = info['phone']
            e = info['email']
            this_otp = info['otp']
            o = Otp.objects.get(email=e)
            if o.otp != this_otp:
                return my_response(False, 'confirmation code invalid', None)

            if time_diff(get_hour_minute(), o.expiry) > 5:
                o.delete()
                return my_response(False, 'confirmation code invalid, try from first', None)

            user = User(
                phone=p,
                email=e,
                name=info['name'],
                password=info['password'],
                private_key=get_random_string(32),
                public_key=get_random_string(32),
            )
            user.save(force_insert=True)
            tok = get_random_string(length=32)
            tok = Token(user=user, token=tok, expiry_date=datetime.datetime.now())
            tok.save()
            o.delete()
            Device.objects.filter(dev_id=info['deviceId']).delete()
            Device(dev_id=info['deviceId'], reg_id=info['deviceToken'], name=p, is_active=True).save()
            return my_response(True, 'user registered', tok.to_json())
        except Exception as e:
            e = str(e)
            if e.__contains__('UNIQUE constraint'):
                return my_response(False, 'user exist! please sign in', {})
            else:
                return my_response(False, 'error in register, check body send, ' + e, {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def login(request):
    if request.method == "POST":
        info = loads(request.body.decode('utf-8'))
        try:
            phone = info['phone']
            user = User.objects.filter(phone=phone)
            if user.exists():
                password = info['password']
                if user[0].password == password:
                    Device(dev_id=info['deviceId'], reg_id=info['deviceToken'], name=phone, is_active=True).save()
                    user.update(status=True)
                    tok = get_random_string(length=32)
                    tok = Token(user=user[0], token=tok, expiry_date=datetime.datetime.now())
                    tok.save(force_insert=True)
                    return my_response(True, 'success', tok.to_json())
                else:
                    return my_response(False, 'invalid information', {})
            else:
                return my_response(False, 'user not found', {})
        except Exception as e:
            e = str(e)
            if e.__contains__('UNIQUE constraint'):
                Device.objects.filter(dev_id=info['deviceId']).delete()
                return login(request)
            return my_response(False, 'error in login, check login body, ' + e, {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def refresh_token(request):
    if request.method == "GET":
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                _now = datetime.datetime.now().date()
                dif = (_now - token[0].expiry_date.date())

                if dif.days < 3:
                    new_token = token[0].user.email + str(datetime.datetime.now())
                    new_token = hashlib.md5(new_token.encode())
                    new_token = new_token.hexdigest()
                    token.update(token=new_token, expiry_date=datetime.datetime.now())
                    return my_response(True, 'success', {'token': new_token})
                else:
                    token.delete()
                    return my_response(False, 'token invalid', {})
            else:
                return my_response(False, 'token not exist', {})
        except Exception as e:
            return my_response(False, 'error in check_expiry_token, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def user_info(request):
    try:
        token = request.headers.get('token')
        token = Token.objects.filter(token=token)
        if token.exists():
            user = token[0].user
            if request.method == 'GET':
                return my_response(True, 'success', user.to_json())
            elif request.method == 'PUT':
                info = loads(request.body.decode('utf-8'))
                p_img = info['profileImage']
                phone = user.phone
                user = User.objects.filter(phone=phone)

                try:
                    img_name = phone + '.png'
                    path = 'media/userImages/' + img_name
                    img_data = base64.b64decode(p_img)
                    with open(path, 'wb') as g:
                        g.write(img_data)
                except Exception as e:
                    img_name = p_img

                user.update(profile_image=img_name)

                return my_response(True, 'success', {})
            else:
                return my_response(False, 'invalid method', {})
        else:
            return my_response(False, 'token not exist', {})
    except Exception as e:
        return my_response(False, 'error in userInfo, ' + str(e), {})


@csrf_exempt
def logout(request):
    if request.method == 'GET':
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                user = token[0].user
                User.objects.filter(phone=user.phone).update(status=False)
                if token[0].is_admin:
                    Device.objects.filter(name='appAdmin').delete()
                token.delete()
                return my_response(True, 'success', {})
            else:
                return my_response(False, 'token not exist', {})
        except Exception as e:
            return my_response(False, 'error in logout, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def delete_account(request):
    if request.method == 'DELETE':
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                user = token[0].user
                User.objects.filter(phone=user.phone).delete()
                token.delete()
                return my_response(True, 'success', {})
            else:
                return my_response(False, 'token not exist', {})
        except Exception as e:
            return my_response(False, 'error in logout, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def password_reminder(request):
    if request.method == 'GET':
        e = request.GET.get('email')
        user = User.objects.filter(email=e)
        if user.exists():
            send_email('your password: ' + user[0].password + ' for pizza app', e)
            return my_response(True, 'your password sent to your email', {})
        else:
            return my_response(False, 'email not exist', {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def my_send_mail(request):
    if request.method == 'GET':
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                receiver_email = token[0].user.email
            else:
                e = request.GET.get('email')
                if e is not None:
                    receiver_email = e
                else:
                    return my_response(False, 'token or email not exist', {})

            otp = random.randint(10000, 99999)
            otp = str(otp)
            send_email('confirmation code: ' + otp + ' for pizza app', receiver_email)
            Otp.objects.filter(email=receiver_email).delete()
            Otp(email=receiver_email, otp=otp, expiry=get_hour_minute()).save()
            return my_response(True, 'success', {})
        except Exception as e:
            return my_response(False, 'error in send mail, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def change_pass(request):
    if request.method == 'POST':
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                user = token[0].user
                info = loads(request.body.decode('utf-8'))

                this_otp = info['otp']
                old = info['old']
                new = info['new']
                o = Otp.objects.get(email=user.email)
                if o.otp != this_otp:
                    return my_response(False, 'confirmation code invalid', None)

                if time_diff(get_hour_minute(), o.expiry) > 5:
                    o.delete()
                    return my_response(False, 'confirmation code invalid, try from first', None)

                if user.password != old:
                    return my_response(False, 'old password invalid', None)

                user = User.objects.filter(phone=user.phone)
                user.update(password=new)
                o.delete()
                return my_response(True, 'success', {})
            else:
                return my_response(False, 'token not exist', {})
        except Exception as e:
            return my_response(False, 'error in all changePass, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def get_home_info(request):
    if request.method == 'GET':
        try:
            user = request.headers.get('token')
            if user is not None:
                user = Token.objects.filter(token=user).first().user
            group_with_children = []
            groups = Group.objects.filter(status=True)
            fav_option = []
            fav_food = []
            for g in groups:
                if g.is_food_g:
                    children = Food.objects.filter(group__group_id=g.group_id, status=True)
                else:
                    children = Option.objects.filter(group__group_id=g.group_id, status=True)
                child_list = []
                for c in children:
                    if g.is_food_g:
                        fav = Favorite.objects.filter(
                            user=user,
                            food=c,
                            option=None,
                        )
                        if fav.exists():
                            fav_food.append(fav[0].food_id)
                            child_list.append(c.to_json(fav=True))
                        else:
                            child_list.append(c.to_json())
                    else:
                        fav = Favorite.objects.filter(
                            user=user,
                            food=None,
                            option=c,
                        )
                        if fav.exists():
                            fav_option.append(fav[0].option_id)
                            child_list.append(c.to_json(fav=True))
                        else:
                            child_list.append(c.to_json())

                group_with_children.append(g.to_json(child_list))

            # if rate number changed go to update food group api and change that
            options = list(Option.objects.filter(rank__gt=4, status=True).order_by('rank'))
            foods = list(Food.objects.filter(rank__gt=4, status=True).order_by('rank'))
            popular_list = merge(foods, options, fav_option, fav_food)

            # To place the special offers at the top of the list
            g_temp = None
            for g in group_with_children:
                if g['name'] == 'Special Offers':
                    g_temp = g
                    group_with_children.remove(g)
                    break
            if g_temp is not None:
                group_with_children.insert(0, g_temp)

            context = {
                'childrenWithGroup': group_with_children,
                'popularFoods': popular_list,
            }
            return my_response(True, 'success', context)
        except Exception as e:
            return my_response(False, 'error in home info, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def get_food_detail(request):
    if request.method == 'GET':
        try:
            food_id = request.GET.get('foodId')
            option_list = []
            food_sizes_list = []
            food_types_list = []
            option_type_list = []

            sizes = FoodSize.objects.filter(food__food_id=food_id)
            for s in sizes:
                food_sizes_list.append(s.to_json())

            types = FoodType.objects.filter(food__food_id=food_id, option_type=None)
            for t in types:
                food_types_list.append(t.to_json())

            op_tys = OptionType.objects.filter(food__food_id=food_id)
            for ot in op_tys:
                l = []
                types = FoodType.objects.filter(option_type=ot)
                for t in types:
                    l.append(t.to_json())
                option_type_list.append(ot.to_json(l))

            fo_options = list(FoodOption.objects.filter(food__food_id=food_id))
            list_peymaeysh = []
            _list = []
            while len(fo_options) != 0:
                fo = fo_options[0]
                list_peymaeysh.append(fo)
                for foo in fo_options:
                    if fo.option_size.option.option_id == foo.option_size.option.option_id \
                            and foo not in list_peymaeysh:
                        list_peymaeysh.append(foo)

                for i in list_peymaeysh:
                    _list.append(i.option_size.to_json())
                    fo_options.remove(i)
                option_list.append(fo.option_size.option.to_json(with_sizes=False, sizes_list=_list))
                list_peymaeysh.clear()
                _list = []
            context = {
                'options': option_list,
                'foodSizes': food_sizes_list,
                'foodTypes': food_types_list,
                'optionTypes': option_type_list,
            }
            return my_response(True, 'success', context)
        except Exception as e:
            return my_response(False, 'getFood detail, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def user_favorite_foods(request):
    token = request.headers.get('token')
    token = Token.objects.filter(token=token)
    if token.exists():
        try:
            user = token[0].user
            if request.method == 'GET':
                favs = Favorite.objects.filter(user=user)
                favs_list = []
                for f in favs:
                    favs_list.append(f.to_json())

                return my_response(True, 'success', favs_list)

            elif request.method == 'POST':
                is_food = request.GET.get('isFood')
                _id = request.GET.get('id')
                fav = request.GET.get('fav')
                fav = int(fav)
                is_food = int(is_food)
                if fav == 1:
                    if is_food == 1:
                        f = Favorite(user=user, food_id=_id)
                        f.save()
                    else:
                        f = Favorite(user=user, option_id=_id)
                        f.save()
                    return my_response(True, 'success', f.to_json())
                else:
                    if is_food == 1:
                        Favorite.objects.filter(user=user, food_id=_id).delete()
                    else:
                        Favorite.objects.filter(user=user, option_id=_id).delete()
                    return my_response(True, 'success', {})

            else:
                return my_response(False, 'invalid method', {})
        except Exception as e:
            return my_response(False, 'error in favorite, ' + str(e), {})

    else:
        return my_response(False, 'token not exist', {})


@csrf_exempt
def get_user_address(request):
    if request.method == 'GET':
        token = request.headers.get('token')
        token = Token.objects.filter(token=token)
        if token.exists():
            user = token[0].user
            ads = Address.objects.filter(user=user)
            ads_list = []
            for a in ads:
                ads_list.append(a.to_json())
            return my_response(True, 'success', ads_list)
        else:
            return my_response(False, 'token not exist', {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def user_address(request, address_id=None):
    token = request.headers.get('token')
    token = Token.objects.filter(token=token)
    if token.exists():
        if request.method == 'POST':
            try:
                user = token[0].user
                info = loads(request.body.decode('utf-8'))

                a = Address(
                    user=user,
                    address=info['address'],
                    building_number=info['buildingNumber'],
                    post_code=info['postCode'],
                    lat=info['lat'],
                    long=info['long']
                )
                a.save()
                return my_response(True, 'success', a.to_json())

            except Exception as e:
                return my_response(False, 'error in insert Address, ' + str(e), {})
        if request.method == 'DELETE':
            Address.objects.filter(address_id=address_id).delete()
            return my_response(True, 'success', {})
        else:
            return my_response(False, 'invalid method', {})
    else:
        return my_response(False, 'invalid token', {})


@csrf_exempt
def res_opening(request):
    # if not RestaurantInfo.objects.first().open:
    #     my_response(True, '', False)
    if request.method == 'GET':
        try:
            res_time = RestaurantTime.objects.first()
            if not res_time.status:
                my_response(True, '', False)

            time_now = str(datetime.datetime.now().time()).split(':')
            time_now = time_now[0] + ':' + time_now[1]

            st = str(res_time.start).split(':')
            st = st[0] + ':' + st[1]

            et = str(res_time.end).split(':')
            et = et[0] + ':' + et[1]

            if not is_between(time_now, (st, et)):
                return my_response(True, '', False)

            return my_response(True, '', True)
        except Exception as e:
            return my_response(False, str(e), {})


@csrf_exempt
def insert_user_order(request):
    if request.method == 'POST':
        try:
            token = request.headers.get('token')
            token = Token.objects.filter(token=token)
            if token.exists():
                user = token[0].user
                info = loads(request.body.decode('utf-8'))
                time = info['datetime']
                if not RestaurantInfo.objects.first().open:
                    return my_response(False, 'The restaurant is closed, Please try later', {})
                if not check_allow_record_order(time):
                    return my_response(False,
                                       'Maximum order is recorded for the restaurant time period, Please try again in a few minutes',
                                       {})
                total_price = info['totalPrice']
                description = info['description']
                address = info['addressId']
                del_time = info['deliveryTime']
                del_datetime = info['deliveryDatetime']
                order_type = info['orderType']
                ser_charge = info['serviceCharge']
                delivery_cost = info['deliveryCost']
                pay_type = info['paymentType']
                is_pre = info['isPreOrder']
                tr_id = random.randint(100000, 100000000)
                order = Order(
                    user=user,
                    track_id=str(tr_id),
                    datetime=time,
                    total_price=total_price,
                    description=description,
                    address_id=address,
                    delivery_time=del_time,
                    delivery_datetime=del_datetime,
                    order_type=order_type,
                    service_charge=ser_charge,
                    delivery_cost=delivery_cost,
                    payment_type=pay_type,
                    is_pre_order=is_pre,
                )
                if is_pre:
                    order.completed = True
                    order.status = True
                else:
                    order.completed = True
                order.save()

                foods = info['foods']
                for f in foods:
                    of = OrderFood(
                        food_size_id=f['foodSizeId'],
                        order=order,
                        number=f['number']
                    )
                    of.save()

                    ts = f['types']
                    for t in ts:
                        OrderType(order_food=of, food_type_id=t).save()
                    food_options = f['foodOptions']
                    for op in food_options:
                        OrderOption(order_food=of, option_size_id=op['id'], option_is_type2=op['optionIsType2']).save()
                options = info['options']
                for o in options:
                    of = OrderFood(food_size_id=o['optionSizeId'], order=order, number=o['number'])
                    of.save()

                title = 'order'
                mess = 'you have a order with trackId: '
                if is_pre:
                    title = 'pre order'
                    mess = 'you have a pre order with trackId: '
                    st = RestaurantTime.objects.first()
                    t = del_datetime.split(' ')[0] + ' ' + str(st.start)
                    date_time_obj = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
                    notif_to_admin_in_background(
                        schedule=date_time_obj.astimezone(),
                        orderId=order.order_id,
                        title=title,
                        message=mess + str(order.track_id),
                    )
                else:
                    notif_to_admin(
                        orderId=order.order_id,
                        title=title,
                        message=mess + str(order.track_id),
                    )

                if 'transactionId' in info:
                    trans_id = info['transactionId']
                    Payment.objects.filter(trans_id=trans_id).update(order=order)

                return my_response(True, 'success', order.to_json())
            else:
                return my_response(False, 'invalid token', {})
        except Exception as e:
            return my_response(False, 'error in insert order, check body send, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def get_orders(request):
    if request.method == 'GET':
        token = request.headers.get('token')
        token = Token.objects.filter(token=token)
        if token.exists():
            if token[0].is_admin:
                orders = Order.objects.all()
            else:
                user = token[0].user
                orders = Order.objects.filter(user=user).order_by('-datetime')

            if token[0].is_admin:
                w_d = False
            else:
                w_d = True
            orders_list = []
            for o in orders:
                orders_list.append(o.to_json(with_detail=w_d))

            return my_response(True, 'success', orders_list)
        else:
            return my_response(False, 'token not exist', {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def request_payment_url(request):
    token = request.headers.get('token')
    token = Token.objects.filter(token=token)
    if token.exists():
        if request.method == 'POST':
            try:
                info = loads(request.body.decode('utf-8'))
                info = pay_level1(info)
                
                if info['outcome']['status'] == 'SUCCESS':
                    user = token[0].user
                    payment = Payment(
                        user=user,
                        trans_id=info['transaction']['transactionId'],
                        status='PENDING',
                        amount=info['transaction']['amount'],
                        trans_time=info['transaction']['transactionTime']
                    )
                    payment.save()
                    
                    context = {
                        'url': info['clientRedirect']['url'],
                        'pareq': info['clientRedirect']['pareq'],
                        'transaction': info['transaction']
                    }
                    
                    return my_response(True, 'success', context)
                else:
                    return my_response(False, info['outcome']['reasonMessage'], info)
                
            except Exception as e:
                return my_response(False, 'your card information is not valid', {})
        else:
            return my_response(False, 'invalid method', {})
    else:
        return my_response(False, 'token not exist', {})


@csrf_exempt
def order_payment(request):
    if request.method == 'POST':
        try:
            trans_id = request.POST.get('MD')
            info = pay_level2(request)

            if 'outcome' in info:
                if info['outcome']['status'] == 'SUCCESS':
                    Payment.objects.filter(trans_id=trans_id).update(status='SUCCESS')
                    return my_response(True, info['outcome']['reasonMessage'], info)
                else:
                    return my_response(False, info['outcome']['reasonMessage'], {})
            else:
                return my_response(False, 'Problem with payment operations, please try later.', info)

        except Exception as e:
            return my_response(False, 'error in payment order, ' + str(e), {})
    elif request.method == 'GET':
        token = request.headers.get('token')
        token = Token.objects.filter(token=token)
        if token.exists():
            if token[0].is_admin:
                pays = Payment.objects.all()
            else:
                pays = Payment.objects.filter(user=token[0].user)
            _list = []
            for p in pays:
                _list.append(p.to_json())
            return my_response(True, 'success', _list)
        else:
            return my_response(False, 'token not exist', {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def set_food_rate(request):
    if request.method == 'POST':
        try:
            info = loads(request.body.decode('utf-8'))
            order_f_id = info['orderFoodId']
            is_food = info['isFood']
            _id = info['id']
            user_rate = info['rate']
            OrderFood.objects.filter(id=order_f_id).update(is_rated=True)

            if is_food:
                c = Food.objects.filter(food_id=_id)
                rate = c[0].rank
                rate = (user_rate + rate) / 2
                c.update(rank=rate)
            else:
                c = Option.objects.filter(option_id=_id)
                rate = c[0].rank
                rate = (user_rate + rate) / 2
                c.update(rank=rate)
            return my_response(True, 'success', {})
        except Exception as e:
            return my_response(False, 'error in set rate, check body send, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def search_food(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        _list = []
        foods = Food.objects.filter(name__contains=name)
        for f in foods:
            if f.status:
                _list.append(f.to_json())

        options = Option.objects.filter(name__contains=name)
        for o in options:
            if o.status:
                _list.append(o.to_json())
        return my_response(True, 'success', _list)
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def filter_food(request):
    if request.method == 'POST':
        try:
            info = loads(request.body.decode('utf-8'))
            food_list = []
            min_p = info['minPrice']
            max_p = info['maxPrice']
            group_name = info['groupName']
            size_name = info['sizeName']
            min_r = info['minRate']
            max_r = info['maxRate']

            groups = Group.objects.filter(name=group_name)
            for g in groups:
                foods = Food.objects.filter(group=g, price__range=(min_p, max_p), rank__range=(min_r, max_r))
                for f in foods:
                    size = FoodSize.objects.filter(food=f, size=size_name)
                    if size.exists():
                        if f.status:
                            food_list.append(f.to_json())

                options = Option.objects.filter(group=g, price__range=(min_p, max_p), rank__range=(min_r, max_r))
                for o in options:
                    size = FoodSize.objects.filter(option=o, size=size_name)
                    if size.exists():
                        if o.status:
                            food_list.append(o.to_json())

            return my_response(True, 'success', food_list)
        except Exception as e:
            return my_response(False, 'error in filter food, check body send, ' + str(e), {})
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def get_res_info(request):
    if request.method == 'GET':
        ress = RestaurantInfo.objects.all()
        for r in ress:
            times_list = []
            times = RestaurantTime.objects.filter(restaurant__res_info_id=r.res_info_id)
            for t in times:
                times_list.append(t.to_json())
            address_list = []
            address = RestaurantAddress.objects.filter(restaurant__res_info_id=r.res_info_id)
            for a in address:
                address_list.append(a.to_json())
            data = r.to_json(times_list, address_list)

            return my_response(True, 'success', data)

        return my_response(False, 'not exist any restaurant', {})

    elif request.method == 'POST' or request.method == 'PUT':
        return admin.res_info(request)
    else:
        return my_response(False, 'invalid method', {})


@csrf_exempt
def ticket(request):
    token = request.headers.get('token')
    token = Token.objects.filter(token=token)
    if token.exists():
        user = token[0].user
        try:
            if request.method == 'POST':
                info = loads(request.body.decode('utf-8'))
                mess = info['message']
                rate = info['rate']

                t = Ticket(user=user, message=mess, rate=rate)
                t.save()
                return my_response(True, 'success', t.to_json())

            elif request.method == 'GET':
                if token[0].is_admin:
                    ticks = Ticket.objects.all()
                else:
                    ticks = Ticket.objects.filter(user=user)
                _list = []
                for t in ticks:
                    _list.append(t.to_json())
                return my_response(True, 'success', _list)
            else:
                return my_response(False, 'invalid method', {})
        except Exception as e:
            return my_response(False, 'error in ticket, check body send, ' + str(e), {})
    else:
        return my_response(False, 'token invalid', {})


