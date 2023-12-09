import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { fetchShoppingLists, saveShoppingList } from "../utils";

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
 
  {
    id: 6,
    name: "leite",
  },
  {
    id: 7,
    name: "ovos",
  },
  {
    id: 8,
    name: "pão de forma",
  },
  {
    id: 9,
    name: "queijo",
  },
 
];

const ShoppingList = () => {

    
    const [products, setProducts] = useState([]);
    const [initialProducts, setInitialProducts] = useState([]);
    const [shoppingList, setShoppingList] = useState(null);
    const [shoppingLists, setShoppingLists] = useState(null);
    const [svShoppingList, setSvShoppingList] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const { id } = useParams();
    const location = useLocation();
    const type = new URLSearchParams(location.search).get('type');
    const navigate = useNavigate();

    let currentURL = window.location.href;
    console.log(currentURL);
  
    const errorMessage= "Error couldn't find it";

    const [userid, setUserid] = useState(null);
    const { ipcRenderer } = window.require('electron');
 
    useEffect(() => {
  
      const handleIdResponse = (event, id) => {
          console.log('Received ID:', id);
          setUserid(id);
       
      };
  
      ipcRenderer.send('getId', 'get id');
      ipcRenderer.on('getIdResponse', handleIdResponse);
  
      
      return () => {
          ipcRenderer.removeListener('getIdResponse', handleIdResponse);
      };
  }, [userid]);

    ipcRenderer.on('zmqMessage', (event, information) => {
        
      if (information.type == "REPLY" && information.body != errorMessage) {
        setShoppingList(information.body)
        const itemsArray = Object.entries(information.body.items).map(([name, details]) => ({
          id: allProducts.find((product) => product.name === name).id,
        
          name: name,
          quantity: details.quantity,
          timestamps: details.timestamps
      }));

      setProducts(itemsArray);
      setInitialProducts(itemsArray);
      // Change remote to local
      navigate(`/shopping-list/${id}?type=local`);
      

        
    }})

    
    useEffect(() => {
      if(userid == null) return;

      if(type === "remote"){
        ipcRenderer.send('frontMessage', {body: id, type: "GET"});
      }

      const fetchData = async () => {
          try {
              const data = await fetchShoppingLists(userid);
              setShoppingLists(data);
              if(data){
                

                  data.ShoppingLists.map((shoppingList) => {

                      if(shoppingList.uuid === id){
                          setShoppingList(shoppingList);
                          

                          const itemsArray = Object.entries(shoppingList.items).map(([name, details]) => ({
                            id: allProducts.find((product) => product.name === name).id,
                          
                            name: name,
                            quantity: details.quantity,
                            timestamps: details.timestamps
                        }));

                          setProducts(itemsArray);
                          setInitialProducts(itemsArray);
                          
                      }
                  })
              }
             
          } catch (error) {
              // Handle errors or display a message to the user
          }
      };

      fetchData();
   
 
  }, [userid]);
    
    // Function to update quantity
    const handleQuantityChange = (id, newQuantity) => {
      setProducts((prevProducts) =>
        prevProducts.map((product) =>
          product.id === id ? { ...product, quantity: parseInt(newQuantity) } : product
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
          if (!productExists) {
              product.quantity = 1;
              product.timestamps = {
                [userid]: 0,
              }
              setProducts([...products, product]);
             
          }
          else if(productExists.quantity === 0){
              productExists.quantity = 1;
              productExists.timestamps = {
                [userid]: Object.entries(productExists.timestamps)[0][1],
              }
              setProducts([...products]);
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
    if(products[0]){
      console.log(Object.entries(products[0].timestamps)[0][0])
    }
    let new_items = []
    for (let i = 0; i < products.length; i++) {
      new_items.push({
        name: products[i].name,
        quantity: products[i].quantity,
        timestamps: {
          [userid]: Object.entries(products[i].timestamps)[0][1] + 1,
        }
      })
    }
      
   
    console.log(products)
    const saveToLocal = () => {
      console.log("saving to local")

      console.log()
      saveShoppingList(userid, id, { 
        uuid: id,
        items: products.reduce((acc, product) => {
        const currentTimestamp = Object.entries(product.timestamps)[0][1];
        let newid = Object.entries(product.timestamps)[0][0];

        let updatedTimestamp;
        if(initialProducts.find((prod) => prod.id === product.id)){
          if(product.quantity !== initialProducts.find((prod) => prod.id === product.id).quantity){
            updatedTimestamp = currentTimestamp + 1;
            newid = userid
          }
          else{
            updatedTimestamp = currentTimestamp;
          }
        
        }
        else{
          updatedTimestamp = currentTimestamp + 1;
        }
        

        acc[product.name] = {
            quantity: product.quantity,
            timestamps: {
              [newid]: updatedTimestamp,
            }
        };
        return acc;
    }, {})});
  };
  const syncServer = () => {
    console.log("syncing to server")
    console.log(shoppingList)
    //ipcRenderer.send('frontMessage', {body: {uuid: id, items: new_items}, type: "PUT"});
  }

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
                <th style={{ width: "15%" }}>Product</th>
                <th style={{ width: "10%" }}>Quantity</th>
              
                <th>Version</th>
                <th>Action</th>
                <th>Last updated by</th>
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
                  
                  <td className="version" data-th="" style={{ width: "10%" }}>
                    {Object.entries(product.timestamps)[0][1]}
                  </td>
                  <td className="actions" data-th="" style={{ width: "10%" }}>
                    
                        <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleRemoveProduct(product.id)} // Handle remove when button is clicked
                        >
                            <FontAwesomeIcon icon={faTrash} />
                        </button>
                  </td>
                  <td  className="last-updated" data-th="">
                    {Object.entries(product.timestamps)[0][0]}
                  </td>
                 
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>
                  <a href="#home" className="btn btn-info text-white">
                    Go Back
                  </a>
                </td>
       
                <td colSpan="1" className="hidden-xs text-center" style={{ width: "10%" }}>
                  <strong>Total: <span className="total">{calculateTotal()}</span></strong>
                </td>
                <td colSpan="1" className="hidden-xs text-center" style={{ width: "10%" }}>
                </td>
                <td>
                      <button onClick={saveToLocal} className="btn btn-success btn-block sync">
                            Local Save
                      </button>
                </td>
                <td>
                      <button  onClick={syncServer} className="btn btn-secondary btn-block sync">
                            Sync Server
                      </button>
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
