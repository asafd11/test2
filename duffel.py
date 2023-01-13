from duffel_api import Duffel
from duffel_api.models import PaymentIntent
from datetime import date
import config

def calc_age(born):
  today = date.today()
  return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
def booking(msg_from,flight_info,passenger_info):
 # buildstr="fly_from:{} fly_to:{} departure:{} returning:{}".format(arr_list[0],arr_list[1],arr_list[2],arr_list[3])
  duffel = Duffel(access_token=config.duffel_us_token)
  slices = [
    {
      "origin": "{}".format(flight_info[0]),
      "destination": "{}".format(flight_info[1]),
      "departure_date": "{}".format(flight_info[2])
    },
    {
      "origin": "{}".format(flight_info[1]),
      "destination": "{}".format(flight_info[0]),
      "departure_date": "{}".format(flight_info[3])
    }
  ]
  calcage=calc_age(passenger_info[-1])
  passengers = [{ "type": "adult" }, { "age": calcage }]
  offers_list =duffel.offer_requests.create().slices(slices).passengers([{"type": "adult"}]).return_offers().execute()
  minprice=0
  min_id=0
  bestoffer=0
  for offer_obj in offers_list.offers:
      #print(offer_obj.total_currency)
      if minprice==0:
          minprice=float(offer_obj.total_amount)
          min_id=offer_obj.id
          bestoffer=offer_obj
          continue
      if minprice>float(offer_obj.total_amount):
          minprice=float(offer_obj.total_amount)
          min_id=offer_obj.id
          bestoffer=offer_obj




  print(minprice)
  print(min_id)
  currecies_type=bestoffer.total_currency
  try:
    selectedoffer=duffel.offers.get(min_id)
  except Exception as error:
    if "Requested offer is no longer available" in error.message:
      print(error.message)
      return booking(msg_from,flight_info,passenger_info)

  passenger_id=selectedoffer.passengers[0].id
  passengerss_info = [
    {
      "phone_number": "+{}".format(passenger_info[0]),
      "email": "{}".format(passenger_info[4]),
      "born_on": "{}".format(passenger_info[-1]),
      "title": "{}".format(passenger_info[5]),
      "gender": "{}".format(passenger_info[6]),
      "family_name": "{}".format(passenger_info[3]),
      "given_name": "{}".format(passenger_info[2]),
      "id": "{}".format(passenger_info[1])
    }
  ]

  payments = [
    {
      "type": "balance",
      "currency": "{}".format(currecies_type),
      "amount": "{}".format(minprice)
    }
  ]
  #res=duffel.orders.create().selected_offers([min_id]).passengers(passengerss_info).payments(payments)



  # convert to duffel account currencies  
  #currecies_exchange=0.85 # from app currencie back to offer currecies
  #user_currecies_to_euro=1.1349  # get exchange price  from offer currecies to euro
  app_take=3
  duffel_take=0.029 # duffel take 2.9%
  #minprice_in_euro=minprice*user_currecies_to_euro
  #calc=(minprice_in_euro+app_take)/(1-duffel_take)
  calc2=(minprice+app_take)/(1-duffel_take) # price of offer + app take 
  format_float = "{:.2f}".format(calc2)
  payment={"amount":"{}".format(format_float),"currency" : "{}".format(currecies_type)}
  print(payment)
  create_payment_int=duffel.payment_intents.create().payment(payment).execute()
  orderid=create_payment_int.id
  client_token=create_payment_int.client_token
  url="{}/duffel/payment.php?ofrom={}&oto={}&fdate={}&rfrom={}&rto={}&rdate={}&cost={}".format(config.base_url,flight_info[0],flight_info[1],flight_info[2],flight_info[1],flight_info[0],flight_info[3],float(round(calc2,2)))
  insertquery="INSERT INTO `orders`(`client_token`, `id`, `phone`, `payment`, `currecies`, `payment_status`, `offerid`, `passenger_id`) VALUES ('{}','{}','{}','{}','{}','0','{}','{}')".format(client_token,orderid,passenger_info[0],minprice,currecies_type,min_id,passenger_id)
  return url,insertquery





