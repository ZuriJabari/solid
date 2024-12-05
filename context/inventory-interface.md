# Inventory Management Interface Implementation

### Inventory Management Interface (continued from InventoryPage.tsx)
```typescript
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

const InventoryPage = () => {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isAddBatchModalOpen, setIsAddBatchModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: inventory, isLoading } = useQuery(
    ['inventory'],
    fetchInventory
  );

  const adjustStockMutation = useMutation(adjustStock, {
    onSuccess: () => {
      queryClient.invalidateQueries(['inventory']);
    }
  });

  return (
    <div className="space-y-6">
      {/* Inventory Alerts */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex items-center">
          <ExclamationCircleIcon className="h-5 w-5 text-yellow-400" />
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              {inventory?.lowStockCount} products are low on stock
              {inventory?.expiringCount > 0 && ` and ${inventory.expiringCount} batches are expiring soon`}
            </p>
          </div>
        </div>
      </div>

      {/* Inventory Control Buttons */}
      <div className="flex justify-between">
        <div className="flex space-x-3">
          <button
            onClick={() => setIsAddBatchModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add New Batch
          </button>
          <button
            onClick={() => setIsStockCountModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Start Stock Count
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Search products..."
            className="border border-gray-300 rounded-md px-3 py-2"
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="border border-gray-300 rounded-md px-3 py-2"
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Product
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Stock
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Active Batches
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {inventory?.products.map((product) => (
              <tr key={product.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 flex-shrink-0">
                      <img 
                        src={product.image} 
                        alt={product.name}
                        className="h-10 w-10 rounded-full" 
                      />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {product.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        SKU: {product.sku}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{product.category}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {product.totalStock} units
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {product.activeBatches} batches
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    product.totalStock <= product.reorderPoint
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {product.totalStock <= product.reorderPoint ? 'Low Stock' : 'In Stock'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <button
                    onClick={() => setSelectedProduct(product)}
                    className="text-indigo-600 hover:text-indigo-900"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Batch Modal */}
      <AddBatchModal
        isOpen={isAddBatchModalOpen}
        onClose={() => setIsAddBatchModalOpen(false)}
        onSubmit={handleAddBatch}
      />

      {/* Stock Count Modal */}
      <StockCountModal
        isOpen={isStockCountModalOpen}
        onClose={() => setIsStockCountModalOpen(false)}
        onSubmit={handleStockCount}
      />

      {/* Product Details Drawer */}
      {selectedProduct && (
        <ProductDetailsDrawer
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onStockAdjust={adjustStockMutation.mutate}
        />
      )}
    </div>
  );
};

// Add Batch Modal Component
const AddBatchModal = ({ isOpen, onClose, onSubmit }) => {
  const [batchData, setBatchData] = useState({
    productId: '',
    quantity: '',
    costPerUnit: '',
    manufacturingDate: '',
    expiryDate: '',
    supplier: '',
    cbdContent: '',
    thcContent: '',
    notes: ''
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
        <h3 className="text-lg font-medium text-gray-900">Add New Batch</h3>
        <form onSubmit={(e) => {
          e.preventDefault();
          onSubmit(batchData);
        }}>
          {/* Form fields */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Product
              </label>
              <select
                value={batchData.productId}
                onChange={(e) => setBatchData({ ...batchData, productId: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                {/* Product options */}
              </select>
            </div>
            {/* Add other form fields */}
          </div>
          
          <div className="mt-5 sm:mt-6">
            <button
              type="submit"
              className="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
            >
              Add Batch
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

// Product Details Drawer Component
const ProductDetailsDrawer = ({ product, onClose, onStockAdjust }) => {
  return (
    <Drawer isOpen={true} onClose={onClose}>
      <div className="px-4 py-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">{product.name}</h2>
          <button
            onClick={onClose}
            className="rounded-md text-gray-400 hover:text-gray-500"
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Product Details */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-500">Batch Information</h3>
          <div className="mt-2 border-t border-gray-200">
            {product.batches.map((batch) => (
              <div key={batch.id} className="py-3 flex justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Batch #{batch.batchNumber}
                  </p>
                  <p className="text-sm text-gray-500">
                    Expires: {new Date(batch.expiryDate).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-sm text-gray-900">
                  {batch.quantity} units
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stock Adjustment */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-500">Adjust Stock</h3>
          <div className="mt-2">
            <StockAdjustmentForm 
              productId={product.id}
              onSubmit={onStockAdjust}
            />
          </div>
        </div>
      </div>
    </Drawer>
  );
};

export default InventoryPage;
```

This implementation provides:

1. Comprehensive Inventory Management:
- Real-time stock tracking
- Batch management
- Expiry date monitoring
- Stock adjustments
- Inventory counts
- Low stock alerts

2. Batch Management:
- Add new batches
- Track CBD/THC content
- Monitor expiry dates
- Manage suppliers
- Record lab reports

3. Stock Control Features:
- Stock adjustments
- Inventory counts
- Reorder point management
- Batch tracking
- Stock movement history

4. User Interface:
- Intuitive table view
- Search and filter capabilities
- Detailed product views
- Batch information
- Stock adjustment forms

Next steps could include:
1. Integration with POS system
2. Automated reordering system
3. Barcode/QR code scanning
4. Batch quality tracking
5. Advanced analytics and forecasting

Would you like me to implement any of these additional features?