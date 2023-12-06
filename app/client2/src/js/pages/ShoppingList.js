import React, { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useParams } from 'react-router-dom'
const initialProducts = [
  {
    id: 1,
    name: "Bananas",
    price: 2,
    image:  "./assets/banana.jpg",
    quantity: 0,
  },
  {
    id: 2,
    name: "Milk",
    price: 3.5,
    image:  "./assets/banana.jpg",
    quantity: 0,
  },
  {
    id: 3,
    name: "Eggs",
    price: 5,
    image:  "./assets/banana.jpg",
    quantity: 0,
  },
  {
    id: 4,
    name: "Bread",
    price: 2.5,
    image:  "./assets/banana.jpg",
    quantity: 0,
  },
  {
    id: 5,
    name: "Apples",
    price: 1,
    image:  "./assets/banana.jpg",
    quantity: 0,
  },
];

const ShoppingList = () => {
    const [products, setProducts] = useState(initialProducts);
    const [searchTerm, setSearchTerm] = useState("");
    const { id } = useParams(); // Get the ID from the URL
    console.log("id", id);
  
    // Function to update quantity
    const handleQuantityChange = (id, newQuantity) => {
      setProducts((prevProducts) =>
        prevProducts.map((product) =>
          product.id === id ? { ...product, quantity: newQuantity } : product
        )
      );
    };
  
    // Calculate subtotal for each product
    const calculateSubtotal = (product) => {
      return product.price * product.quantity;
    };
  
    // Calculate total price
    const calculateTotal = () => {
      return products.reduce(
        (total, product) => total + calculateSubtotal(product),
        0
      );
    };
  
    // Filter products based on search term
    const filteredProducts = products.filter((product) =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

  return (
    <div className="container main-section">
      <div className="row">
      <div className="col-lg-12 mb-3">
        <input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
        <div className="col-lg-12 pb-2">
          <h4>Shopping Cart</h4>
        </div>
        <div className="col-lg-12 pl-3 pt-3">
          <table className="table table-hover border bg-white">
            <thead>
              <tr>
                <th>Product</th>
                <th>Price</th>
                <th style={{ width: "10%" }}>Quantity</th>
                <th>Subtotal</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((product) => (
                <tr key={product.id}>
                  <td>
                    <div className="row">
                      <div className="Product-img">
                        <img
                          src={product.image}
                          alt="..."
                          className="img-responsive"
                        />
                      </div>
                      <div className="">
                        <h4 className="nomargin">{product.name}</h4>
                      </div>
                    </div>
                  </td>
                  <td className="price">{product.price}</td>
                  <td data-th="Quantity">
                    <input
                      type="number"
                      className="form-control text-center"
                      value={product.quantity}
                      onChange={(e) =>
                        handleQuantityChange(product.id, e.target.value)
                      }
                    />
                  </td>
                  <td className="subtotal">
                    {calculateSubtotal(product)}
                  </td>
                  <td className="actions" data-th="" style={{ width: "10%" }}>
                    
                    <button className="btn btn-danger btn-sm">
                        <FontAwesomeIcon icon={faTrash} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>
                  <a href="#" className="btn btn-info text-white">
                    Go Back
                  </a>
                </td>
                <td colSpan="2" className="hidden-xs"></td>
                <td className="hidden-xs text-center" style={{ width: "10%" }}>
                  <strong>Total: <span className="total">{calculateTotal()}</span></strong>
                </td>
                <td>
                  <a href="#" className="btn btn-success btn-block">
                    Save
                  </a>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ShoppingList;
