# Python Mycelium Gear API
Access all API features of https://gear.mycelium.com. API documentation is available at https://admin.gear.mycelium.com/docs

Create a bitcoin payment gateway for your eshop. Create custom orders with Mycelium Gear Gateway.

![Mycelium Gear Payment Gateway](http://i.imgur.com/a79MjSo.png)

## Create new Gateway 
In order to use Mycelium Gear API you need to get a gateway ID and secret. Create new gateway [here](https://admin.gear.mycelium.com/gateways/new). 

Don't forget to save your gateway secret somewhere safe!

## Examples

### Prepare class object

```python
from mycelium_gear import MyCeliumGear 
mg = MyCeliumGear(MYCELIUMGEAR_GATEWAY_ID, MYCELIUMGEAR_GATEWAY_SECRET)
```

### Create order
```python
amount = 30  # 30$ for example
keychain_id = 0

order = mg.create_order(amount, keychain_id)

order_id = order['order_id']  # Needed for callback requests
payment_id = order['payment_id']  # Needed for cancelling and fetching order
```

### Cancel order
```python
mg.cancel_order(payment_id)
```

### Manualy Check order status
```python
order = mg.check_order(payment_id)
```

### Check order status from Gear's webhook
flask implement
```python
@app.route('/mycelium/callback')
def mycelium_callback():
    if mg.is_order_callback_valid('GET',
                                  request.url, 
                                  request.headers.get('X-Signature')):
        
        data = request.args
        # work with data
        order_status = data['status']
        # and so on...
    return '', 200
```

## Support me
Bitcoin donations are welcome at [1BDF5Uyo8PXRMXiRCv2njktdQJZhxEPvaY](https://blockchain.info/address/1BDF5Uyo8PXRMXiRCv2njktdQJZhxEPvaY). Thank you!