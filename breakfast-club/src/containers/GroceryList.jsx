import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getIdToken } from '../utils/auth';

const GroceryList = () => {
  const [groceryItems, setGroceryItems] = useState([]);
  const [checkedItems, setCheckedItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGroceryItems();
  }, []);

  const fetchGroceryItems = async () => {
    try {
      const token = await getIdToken();
      const response = await axios.get('http://45.56.112.26:6969/grocery/items', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.status === 'success') {
        setGroceryItems(response.data.items);
      }
    } catch (err) {
      setError('Failed to fetch grocery items');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const updateGroceryItems = async (items) => {
    try {
      const token = await getIdToken();
      await axios.post('http://45.56.112.26:6969/grocery/items', 
        { items },
        { headers: { Authorization: `Bearer ${token}` }}
      );
    } catch (err) {
      setError('Failed to update grocery items');
      console.error(err);
    }
  };

  const toggleItem = (index) => {
    setCheckedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const removeItem = async (index) => {
    const updatedItems = groceryItems.filter((_, i) => i !== index);
    setGroceryItems(updatedItems);
    await updateGroceryItems(updatedItems);
  };

  const clearCheckedItems = async () => {
    const remainingItems = groceryItems.filter((_, index) => !checkedItems[index]);
    setGroceryItems(remainingItems);
    setCheckedItems({});
    await updateGroceryItems(remainingItems);
  };

  const clearAllItems = async () => {
    setGroceryItems([]);
    setCheckedItems({});
    await updateGroceryItems([]);
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-warning" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">
          <i className="bi bi-exclamation-circle me-2"></i>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold mb-0">Grocery List</h2>
        <div className="d-flex gap-2">
          <button 
            className="btn btn-warning" 
            onClick={clearCheckedItems}
            disabled={!Object.keys(checkedItems).length}
          >
            Clear Checked Items
          </button>
          <button 
            className="btn btn-danger" 
            onClick={clearAllItems}
            disabled={!groceryItems.length}
          >
            Clear All
          </button>
        </div>
      </div>

      {groceryItems.length === 0 ? (
        <div className="alert alert-info">
          <i className="bi bi-info-circle me-2"></i>
          Your grocery list is empty.
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="list-group list-group-flush">
            {groceryItems.map((item, index) => (
              <div key={index} className="list-group-item d-flex align-items-center">
                <div className="form-check flex-grow-1">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    checked={checkedItems[index] || false}
                    onChange={() => toggleItem(index)}
                  />
                  <label 
                    className="form-check-label ms-2"
                    style={{ 
                      textDecoration: checkedItems[index] ? 'line-through' : 'none',
                      color: checkedItems[index] ? '#6c757d' : 'inherit'
                    }}
                  >
                    {item}
                  </label>
                </div>
                <button 
                  className="btn btn-link text-danger"
                  onClick={() => removeItem(index)}
                >
                  <i className="bi bi-trash"></i>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GroceryList;