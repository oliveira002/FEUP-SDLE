import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useParams } from 'react-router-dom'
import { fetchShoppingLists } from "../shoppingListOperations";
const allProducts = [
  {
    id: 1,
    name: "bananas",
  },
  {
    id: 2,
    name: "cebolas",
  },
  {
    id: 3,
    name: "ovos",
  },
  {
    id: 4,
    name: "pão",
  },
  {
    id: 5,
    name: "maçãs",
  },

 


];

const ShoppingList = () => {
    const [products, setProducts] = useState([]);
    const [shoppingList, setShoppingList] = useState(null);
    const [shoppingLists, setShoppingLists] = useState(null);
    const [svShoppingList, setSvShoppingList] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const { id } = useParams(); // Get the ID from the URL
    const userid = 1;

    const { ipcRenderer } = window.require('electron');
    
    useEffect(() => {
      ipcRenderer.send('frontMessage', {body: id, type: "GET"});

      const fetchServerData = async () => {
        ipcRenderer.on('zmqMessage', (event, information) => {
          let parsed = JSON.stringify(information)
          if (parsed.type == "REPLY") {
            setSvShoppingList(parsed)
            console.log(parsed)
          }
        });
      }

      const fetchData = async () => {
          try {
              const data = await fetchShoppingLists(userid);
              setShoppingLists(data);
              if(data){

                  data.ShoppingLists.map((shoppingList) => {
                    console.log("shoppingList", shoppingList);
                      if(shoppingList.uuid === id){
                          console.log("shoppingList", shoppingList.items);
                          setShoppingList(shoppingList);

                          const itemsArray = Object.entries(shoppingList.items).map(([name, details]) => ({
                            id: allProducts.find((product) => product.name === name).id,
                          
                            name: name,
                            quantity: details.quantity,
                        }));
                          console.log("itemsArray", itemsArray);
                          setProducts(itemsArray);
                          
                      }
                  })
              }
             
          } catch (error) {
              // Handle errors or display a message to the user
          }
      };

      fetchData();
      fetchServerData()
  }, []);
    
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
      return  product.quantity;
    };

    const [selectedProduct, setSelectedProduct] = useState(null);

    // Function to handle adding a product to the list
    const handleAddProduct = (product) => {
      if (product) {
          const productExists = products.find(prod => prod.id === product.id);
          if (!productExists || productExists.quantity === 0) {
              product.quantity = 1;
              const set = new Set(products);
              set.add(product);
              setProducts([...set]);
          }
      }
  };

  const handleRemoveProduct = (id) => {
    // quantity to 0
      const updatedProducts = products.map(product => {
          if (product.id === id) {
              product.quantity = 0;
          }
          return product;
      });

      setProducts(updatedProducts);
  };
  
    // Calculate total quantity
    const calculateTotal = () => {
      return products.reduce(
        (total, product) => total + parseInt(calculateSubtotal(product)),
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
            <div>
                {/* Display all products when search term is present */}
                {searchTerm && allProducts
                    .filter(product => product.name.toLowerCase().includes(searchTerm.toLowerCase()))
                    .map(product => (
                        <button
                            key={product.id}
                            onClick={() => handleAddProduct(product)} // Use onClick to handle the click event
                            className="btn btn-primary btn-sm mr-2 mb-2"
                        >
                            {product.name}
                        </button>
                    ))
                }
            </div>
      </div>
        <div className="col-lg-12 pb-2">
          <h4>Shopping Cart</h4>
        </div>
        <div className="col-lg-12 pl-3 pt-3">
          <table className="table table-hover border bg-white">
            <thead>
              <tr>
                <th>Product</th>
                <th style={{ width: "10%" }}>Quantity</th>
                <th>Subtotal</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {products && products.map((product) => (
                product.quantity > 0 &&
                <tr key={product.id}>
                  <td>
                    <div className="row">
                      
                      <div className="">
                        <h5 className="nomargin">{product.name}</h5>
                      </div>
                    </div>
                  </td>

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
                    
                        <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleRemoveProduct(product.id)} // Handle remove when button is clicked
                        >
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
                <td colSpan="1" className="hidden-xs"></td>
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
