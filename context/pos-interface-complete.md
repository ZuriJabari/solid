# POS Interface Implementation (Continued)

```typescript
// Continuing from the cart section in POSPage.tsx

const POSPage = () => {
  // ... previous code ...

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Product Selection section from before */}

      {/* Cart Section */}
      <div className="w-96 bg-white border-l">
        <div className="h-full flex flex-col">
          <div className="p-4 border-b">
            <h2 className="text-lg font-medium">Current Order</h2>
            {session && (
              <p className="text-sm text-gray-500">
                Cashier: {session.cashier_name}
              </p>
            )}
          </div>

          <div className="flex-1 overflow-auto p-4">
            {cart.map(item => (
              <div key={item.product.id} className="flex items-center mb-4 bg-gray-50 p-3 rounded">
                <div className="flex-1">
                  <h3 className="font-medium">{item.product.name}</h3>
                  <p className="text-sm text-gray-500">
                    ${item.product.price} x {item.quantity}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                    className="p-1 rounded-full hover:bg-gray-200"
                  >
                    <MinusIcon className="h-5 w-5" />
                  </button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                    className="p-1 rounded-full hover:bg-gray-200"
                  >
                    <PlusIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => removeFromCart(item.product.id)}
                    className="p-1 rounded-full hover:bg-gray-200 text-red-500"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="border-t p-4 bg-gray-50">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${calculateTotals().subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax (18%)</span>
                <span>${calculateTotals().tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span>${calculateTotals().total.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={() => setShowPaymentModal(true)}
              disabled={cart.length === 0}
              className="w-full mt-4 py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
            >
              Proceed to Payment
            </button>
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        total={calculateTotals().total}
        onComplete={handlePayment}
      />
    </div>
  );
};

// Payment Modal Component
const PaymentModal = ({ isOpen, onClose, total, onComplete }) => {
  const [paymentMethod, setPaymentMethod] = useState('');
  const [amountReceived, setAmountReceived] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');

  const paymentMethods = [
    { id: 'CASH', name: 'Cash', icon: CashIcon },
    { id: 'CARD', name: 'Card', icon: CreditCardIcon },
    { id: 'MOBILE_MONEY', name: 'Mobile Money', icon: PhoneIcon },
  ];

  const handleSubmit = () => {
    onComplete({
      paymentMethod,
      amountReceived: parseFloat(amountReceived),
      customerPhone
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <h2 className="text-xl font-bold mb-4">Payment</h2>
        
        {/* Payment Method Selection */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {paymentMethods.map(method => (
            <button
              key={method.id}
              onClick={() => setPaymentMethod(method.id)}
              className={`p-4 rounded-lg border ${
                paymentMethod === method.id
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200'
              }`}
            >
              <method.icon className="h-8 w-8 mx-auto mb-2" />
              <span className="block text-center">{method.name}</span>
            </button>
          ))}
        </div>

        {/* Payment Details */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Total Amount
            </label>
            <div className="mt-1 text-2xl font-bold">
              ${total.toFixed(2)}
            </div>
          </div>

          {paymentMethod === 'CASH' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Amount Received
              </label>
              <input
                type="number"
                value={amountReceived}
                onChange={(e) => setAmountReceived(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              />
              {parseFloat(amountReceived) > total && (
                <div className="mt-2">
                  Change: ${(parseFloat(amountReceived) - total).toFixed(2)}
                </div>
              )}
            </div>
          )}

          {paymentMethod === 'MOBILE_MONEY' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Customer Phone Number
              </label>
              <input
                type="tel"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              />
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!paymentMethod || (paymentMethod === 'CASH' && !amountReceived)}
            className="flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
          >
            Complete Payment
          </button>
        </div>
      </div>
    </Modal>
  );
};

// Receipt Modal Component
const ReceiptModal = ({ isOpen, onClose, orderData }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold">CBD Store</h2>
          <p className="text-sm text-gray-500">
            Order #{orderData.orderNumber}
          </p>
          <p className="text-sm text-gray-500">
            {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}
          </p>
        </div>

        <div className="border-t border-b py-4 mb-4">
          {orderData.items.map(item => (
            <div key={item.id} className="flex justify-between mb-2">
              <div>
                <span className="font-medium">{item.product.name}</span>
                <span className="text-sm text-gray-500 block">
                  ${item.price} x {item.quantity}
                </span>
              </div>
              <span>${(item.price * item.quantity).toFixed(2)}</span>
            </div>
          ))}
        </div>

        <div className="space-y-2 mb-6">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>${orderData.subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Tax</span>
            <span>${orderData.tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold">
            <span>Total</span>
            <span>${orderData.total.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-500">
            <span>Payment Method</span>
            <span>{orderData.paymentMethod}</span>
          </div>
        </div>

        <div className="text-center text-sm text-gray-500">
          <p>Thank you for your purchase!</p>
          <p>Please retain this receipt for your records.</p>
        </div>

        <div className="mt-6">
          <button
            onClick={() => window.print()}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Print Receipt
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default POSPage;
```

This implementation provides:

1. Complete POS Interface:
- Product selection with categories and search
- Cart management with quantity controls
- Order summary with tax calculation
- Multiple payment methods

2. Payment Processing:
- Cash payments with change calculation
- Card payments
- Mobile money integration
- Receipt generation

3. User Experience Features:
- Real-time total calculation
- Intuitive product grid
- Easy quantity adjustment
- Clear payment flow

4. Receipt Generation:
- Detailed order information
- Tax breakdown
- Payment method details
- Print functionality

The system integrates with the backend services we implemented earlier, providing a complete solution for:
- Inventory management
- Sales tracking
- Payment processing
- Receipt generation

Would you like me to implement additional features such as:
1. End-of-day reporting
2. Cash drawer management
3. Discount handling
4. Customer loyalty integration

Let me know which aspects you'd like to explore next!