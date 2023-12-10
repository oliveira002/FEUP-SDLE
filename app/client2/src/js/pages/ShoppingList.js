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
    name: "pão de forma",
  },
  {
    id: 8,
    name: "queijo",
  },
 
];

const ShoppingList = () => {

    
    const [products, setProducts] = useState([]);
    const [initialProducts, setInitialProducts] = useState([]);
    const [shoppingList, setShoppingList] = useState(null);
    const [shoppingLists, setShoppingLists] = useState(null);
    const [svShoppingList, setSvShoppingList] = useState(null);
    const [serverMessage, setServerMessage] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const { id } = useParams();
    const location = useLocation();
    const type = new URLSearchParams(location.search).get('type');
    const navigate = useNavigate();
    const [newItem, setNewItem] = useState('');
    let currentURL = window.location.href;
    console.log(currentURL);



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
      console.log(information)    

      if (information.type == "REPLY" && information.body === "Modified Shopping List Correctly"){ 
        const example = {"uuid":"815bf169-4d4b-455f-a8b1-b9dadeaea9e3","items":{"bananas":{"quantity":3,"timestamps":{"1231-31-23123-12-33":2}},"cebolas":{"quantity":1,"timestamps":{"1231-31-23123-12-33":2}}}}
        
        const itemsArray = Object.entries(example.items).map(([name, details]) => ({
        
          name: name,
          quantity: details.quantity,
          timestamps: details.timestamps
        }));
        /*if(itemsArray === products){
          setServerMessage("Modified Shopping List Correctly");
          navigate(`/shopping-list/${id}?type=local`);
        }
        else{
          setServerMessage("Local changes were merged with the server");
          setProducts(itemsArray);
          setInitialProducts(itemsArray);
          navigate(`/shopping-list/${id}?type=local`);
        }*/
        setServerMessage("Modified Shopping List Correctly");
        navigate(`/shopping-list/${id}?type=local`);

        
      }
      else if (information.type == "REPLY") {
        setShoppingList(information.body)
        const itemsArray = Object.entries(information.body.items).map(([name, details]) => ({
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
    const handleQuantityChange = (name, newQuantity) => {
      setProducts((prevProducts) =>
        prevProducts.map((product) =>
          product.name === name ? { ...product, quantity: parseInt(newQuantity) } : product
        )
      );
    };

    // Calculate subtotal for each product
    const calculateSubtotal = (product) => {
      return  product.quantity;
    };

    const [selectedProduct, setSelectedProduct] = useState(null);

  

  const handleAddCustomProduct = () => {
    if (newItem.trim() !== '') {
      const productExists = products.find(
        (product) => product.name === newItem.trim()
      );
  
      if (!productExists) {
        const newProduct = {
          name: newItem.trim(),
          quantity: 1,
          timestamps: {
            [userid]: 0,
          },
        };
        setProducts([...products, newProduct]);
        setNewItem(''); // Clear the input field after adding the item
      } else {
        if(productExists.quantity === 0){
  
            productExists.quantity = 1;	
            
            setProducts([...products]);
            }
      }
    }
  };
  console.log(products)

  const handleRemoveProduct = (name) => {

      const updatedProducts = products.map(product => {
          if (product.name === name) {
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
      saveShoppingList(userid, id, { 
        uuid: id,
        items: products.reduce((acc, product) => {
        const currentTimestamp = Object.entries(product.timestamps)[0][1];
        let newid = Object.entries(product.timestamps)[0][0];

        let updatedTimestamp;
        if(initialProducts.find((prod) => prod.name === product.name )){
          if(product.quantity !== initialProducts.find((prod) => prod.name === product.name).quantity){
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

    const desiredFormat = new_items.reduce((acc, product) => {
      const { name, quantity, timestamps } = product;
      acc.items[name] = { quantity, timestamps };
      return acc;    
    }
    , { uuid: id, items: {} });

    
    // Converter para JSON
    const jsonFormat = JSON.stringify(desiredFormat);
    
    console.log(jsonFormat);
  
  
    ipcRenderer.send('frontMessage', {body: jsonFormat, type: "POST"});
    
  }



  return (
    <div className="container main-section">
      <div className="row">
      
      <div className="col-lg-12 mb-3">
        <input
          type="text"
          placeholder="Add item..."
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
        />
        <button
          onClick={handleAddCustomProduct}
          className="btn btn-primary add-product"
        >
          Add
        </button>
      </div>
        <div className="col-lg-12 pb-2">
        <div className="d-flex title">
          <h4>Shopping Cart: </h4>
          {id && (
            <h6>{id}</h6>
          )}
        </div>
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
         
              {products && products.map((product, index) => (
                product.quantity > 0 &&
                <tr key={index}>
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
                        handleQuantityChange(product.name, e.target.value)
                      }
                    />
                  </td>
                  
                  <td className="version" data-th="" style={{ width: "10%" }}>
                    {Object.entries(product.timestamps)[0][1]}
                  </td>
                  <td className="actions" data-th="" style={{ width: "10%" }}>
                    
                        <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleRemoveProduct(product.name)} // Handle remove when button is clicked
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
          {serverMessage && (
                <div className="alert alert-success mt-3" role="alert">
                    {serverMessage}
                </div>
            )
            }
        </div>
      </div>
    </div>
  );
};

export default ShoppingList;
