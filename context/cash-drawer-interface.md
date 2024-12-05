# Cash Drawer Management Interface (Continued)

```typescript
// Continuing CashDrawerPage.tsx
              onClick={() => setShowCashMovement(true)}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded"
            >
              Record Movement
            </button>
            <button
              onClick={() => setShowCashMovement(true)}
              className="flex-1 bg-yellow-600 text-white px-4 py-2 rounded"
            >
              Cash Drop
            </button>
          </div>

          {/* Cash Movements List */}
          <div className="mt-6">
            <h3 className="font-medium mb-4">Recent Movements</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Reference
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activeDrawer.movements.map((movement) => (
                    <tr key={movement.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {new Date(movement.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {movement.movement_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {formatCurrency(movement.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {movement.reference}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {movement.notes}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <h2 className="text-xl font-medium text-gray-900 mb-4">
            No Active Cash Drawer
          </h2>
          <button
            onClick={() => setShowOpenDrawer(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded"
          >
            Open New Drawer
          </button>
        </div>
      )}

      {/* Open Drawer Modal */}
      <OpenDrawerModal
        isOpen={showOpenDrawer}
        onClose={() => setShowOpenDrawer(false)}
        onSubmit={openDrawerMutation.mutate}
      />

      {/* Cash Movement Modal */}
      <CashMovementModal
        isOpen={showCashMovement}
        onClose={() => setShowCashMovement(false)}
        onSubmit={cashMovementMutation.mutate}
      />

      {/* Close Drawer Modal */}
      <CloseDrawerModal
        isOpen={showCloseDrawer}
        onClose={() => setShowCloseDrawer(false)}
        onSubmit={closeDrawerMutation.mutate}
        expectedBalance={activeDrawer?.current_balance || 0}
      />
    </div>
  );
};

// Open Drawer Modal Component
const OpenDrawerModal = ({ isOpen, onClose, onSubmit }) => {
  const [openingBalance, setOpeningBalance] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      opening_balance: parseFloat(openingBalance),
      notes
    });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Open New Cash Drawer
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Opening Balance
              </label>
              <input
                type="number"
                step="0.01"
                value={openingBalance}
                onChange={(e) => setOpeningBalance(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                rows={3}
              />
            </div>
          </div>
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Open Drawer
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

// Cash Movement Modal Component
const CashMovementModal = ({ isOpen, onClose, onSubmit }) => {
  const [movementType, setMovementType] = useState('');
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      movement_type: movementType,
      amount: parseFloat(amount),
      reference,
      notes
    });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Record Cash Movement
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Movement Type
              </label>
              <select
                value={movementType}
                onChange={(e) => setMovementType(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              >
                <option value="">Select Type</option>
                <option value="PAYOUT">Payout</option>
                <option value="DROP">Cash Drop</option>
                <option value="ADD">Add Cash</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Amount
              </label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Reference
              </label>
              <input
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                rows={3}
              />
            </div>
          </div>
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Record Movement
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

// Close Drawer Modal Component
const CloseDrawerModal = ({ isOpen, onClose, onSubmit, expectedBalance }) => {
  const [actualCash, setActualCash] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      actual_cash: parseFloat(actualCash),
      notes
    });
    onClose();
  };

  const difference = actualCash ? parseFloat(actualCash) - expectedBalance : 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Close Cash Drawer
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Expected Balance
              </label>
              <div className="mt-1 text-lg font-medium">
                {formatCurrency(expectedBalance)}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Actual Cash
              </label>
              <input
                type="number"
                step="0.01"
                value={actualCash}
                onChange={(e) => setActualCash(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            {actualCash && (
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Difference
                </label>
                <div className={`mt-1 text-lg font-medium ${
                  difference < 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {formatCurrency(difference)}
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                rows={3}
              />
            </div>
          </div>
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Close Drawer
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default CashDrawerPage;
```

This implementation provides a complete cash drawer management system with:

1. Cash Drawer Operations:
- Opening new drawers with initial balance
- Recording cash movements (payouts, drops, additions)
- Closing drawers with reconciliation
- Detailed movement tracking

2. User Interface Features:
- Clear status displays
- Movement history table
- Easy-to-use modals for operations
- Real-time difference calculation
- Comprehensive notes system

3. Data Validation:
- Required fields enforcement
- Number input validation
- Balance reconciliation
- Movement type tracking

4. UI Components:
- Responsive layout
- Clear status indicators
- Intuitive form controls
- Proper error states

Would you like me to implement additional features such as:
1. Shift reports
2. Cash drawer audit trails
3. Multi-drawer support
4. Advanced reconciliation tools

Let me know which aspects you'd like to explore next!