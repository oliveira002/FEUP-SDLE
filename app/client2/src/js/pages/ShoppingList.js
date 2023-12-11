import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { fetchShoppingLists, saveShoppingList } from "../utils";

import { v4 as uuidv4 } from 'uuid';

class GCounter {
  constructor(counter) {
      this.counter = counter
  }

  static zero() {
      return new GCounter({})
  }

  value() {
      return Object.values(this.counter).reduce((acc, currentValue) => acc + currentValue, 0);
  }

  inc(replica, value) {
  
      if(this.counter[replica] === undefined){

        this.counter[replica] = 0;
      }
      this.counter[replica] += value;
      
     
  }

  static merge(a, b) {

      let keys = Array.from(a.counter.keys()).concat(Array.from(b.counter.keys()))
      const uniqueKeys = new Set(keys);

      let mergedCounter = new Map()
      for (const k of uniqueKeys) {
          mergedCounter.set(k,
              Math.max(
                  (a.counter.get(k) ?? 0),
                  (b.counter.get(k) ?? 0)
              )
          );
      }
      return new GCounter(mergedCounter);
  }

  toString() {
    
    let entries = []
    Object.keys(this.counter).forEach(key => {
      entries.push(`"${key}": ${this.counter[key]}`)
    })

    return `{ ${entries.join(', ')} }`;
  }

}



class Shopping_List{
  constructor(uuid=null) {
      this.items = new Map()
      this.uuid = uuidv4()
      if(uuid !== null) {
          this.uuid = uuid
      }
  }
  static fromJson(json){
    let sl = new Shopping_List()
    sl.uuid = json["uuid"]
  
    let items = new Map()
    Object.keys(json["items"]).forEach(key => {
        let pos = new GCounter(json["items"][key]["pos"])
        
        let neg = new GCounter(json["items"][key]["neg"])

        let pn = new PNCounter(pos, neg)
        items.set(key, pn)
    })
  
    sl.items = items
    return sl
  }

  inc_or_add_item(item_name, quantity, replica){
  
      let item =  this.items.get(item_name) ?? PNCounter.zero()
      item.inc(replica, quantity)
      this.items.set(item_name, item)
      console.log("inc_or_add_item", this)
  }

  dec_item(item_name, quantity, replica){
      let item =  this.items.get(item_name) ?? PNCounter.zero()
      item.dec(replica, quantity)
      this.items.set(item_name, item)
  }

  static merge(a, b){
      let items = Array.from(a.items.keys()).concat(Array.from(b.items.keys()))
      const uniqueItems = new Set(items);

      let mergedItems = new Map()
      for (const item of uniqueItems) {
          mergedItems.set(item,
              PNCounter.merge(
                  (a.items.get(item) ?? PNCounter.zero()),
                  (b.items.get(item) ?? PNCounter.zero())
              )
          );
      }

      // Assuming a.uuid === b.uuid
      let mergedSL = new Shopping_List(a.uuid)
      mergedSL.items = mergedItems
      return mergedSL
  }

  

  toString(){
      let items = Array.from(this.items.entries()).map(([key, value]) => `"${key}": {${value.toString()}}`);
      return "{\"uuid\":\"" + this.uuid + "\", \"items\": {" + items + "}}"
  }


}

class PNCounter{
  constructor(pos, neg) {
      this.pos = pos
      this.neg = neg
  }

  static zero() {
      return new PNCounter(GCounter.zero(), GCounter.zero())
  }

  value(){
      return this.pos.value() - this.neg.value()
  }

  inc(replica, value){
      this.pos.inc(replica, value)
  }

  dec(replica, value){
      this.neg.inc(replica, value)
  }
  static merge(a, b){
      return new PNCounter(GCounter.merge(a.pos, b.pos), GCounter.merge(a.neg, b.neg))
  }

  toString(){
      return "\"pos\":" + this.pos.toString() + ", \"neg\":" + this.neg.toString()
  }

}


const ShoppingList = () => {
    let shopping_list = new Shopping_List();
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
   
    console.log("1",shoppingList)
    

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
      if (information.type == "REPLY_POST"){ 
        saveToLocal();
        console.log("Received message from main process", information.body);
        let shop_list = Shopping_List.fromJson(information.body);
        console.log("shop_list",shop_list)
        setShoppingList(shop_list);
        let itemsArray = [];
        shop_list.items.forEach((value, key) => {
          itemsArray.push({
            name: key,	
            quantity: value.value(),
          })
            
          
        }
        );
     
        setProducts(itemsArray);
        setInitialProducts(itemsArray);
        navigate(`/shopping-list/${id}?type=local`);
        setServerMessage("Modified Shopping List Correctly");

        
        
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
        //setServerMessage("Modified Shopping List Correctly");
        //navigate(`/shopping-list/${id}?type=local`);

        
      }
      else if (information.type == "REPLY_GET") {

        console.log("Received message from main process", information.body);
        let shop_list = Shopping_List.fromJson(information.body);
        console.log("shop_list",shop_list)
        setShoppingList(shop_list);
        let itemsArray = [];
        shop_list.items.forEach((value, key) => {
          itemsArray.push({
            name: key,	
            quantity: value.value(),
          })
            
          
        }
        );

        setProducts(itemsArray);
        setInitialProducts(itemsArray);
        navigate(`/shopping-list/${id}?type=local`);

     
        
        
        
        /*setShoppingList(information.body)
        const itemsArray = Object.entries(information.body.items).map(([name, details]) => ({
          name: name,
          quantity: details.quantity,
          timestamps: details.timestamps
      }));


      setProducts(itemsArray);
      setInitialProducts(itemsArray);
      // Change remote to local
      navigate(`/shopping-list/${id}?type=local`);*/

      

        
    }})

    console.log("1234",initialProducts)
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

                let shop = data.ShoppingLists.find((list) => list.uuid === id);
                
                
                  if(shop){
                    let shop_list = Shopping_List.fromJson(shop);
       

                      setShoppingList(shop_list);
                      
                      console.log("items", shop_list.items)
                      let itemsArray = [];
                      shop_list.items.forEach((value, key) => {
                        itemsArray.push({
                          name: key,	
                          quantity: value.value(),
                        })
                          
                        
                      });
                      
                      setProducts(itemsArray);
                 
                      setInitialProducts(itemsArray);    
                      
                  }
                  else{

                      // Create new shopping list
                      let newShoppingList = new Shopping_List(id);
                
                      let itemsArray = [];
                      newShoppingList.items.forEach((value, key) => {
                        itemsArray.push({
                          name: key,	
                          quantity: value.value(),
                        })
                          
                        
                      });
                      setShoppingList(newShoppingList);
                      setProducts(itemsArray);
                      setInitialProducts(itemsArray);
                      navigate(`/shopping-list/${id}?type=local`);
                  }
              
              }
             
          } catch (error) {
              // Handle errors or display a message to the user
          }
      };

      fetchData();
   
 
  }, [userid]);
    
    // Function to update quantity
    const handleQuantityChange = (name, newQuantity) => {
      newQuantity = parseInt(newQuantity);
 
      setProducts((prevProducts) =>
        prevProducts.map((product) =>
          product.name === name ? { ...product, quantity: newQuantity } : product
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
    console.log("products123",initialProducts)
  };


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
       
      })
    }
      
   
    console.log(products)
    const saveToLocal = () => {


      console.log("initialProducts",initialProducts)
      console.log("products",products)
      products.forEach((product) => {
        let initial_quantity = 0;
        
        try{
          initial_quantity= initialProducts.find((prod) => prod.name === product.name).quantity
        }
        catch{
          initial_quantity = 0;
        }
        let delta = parseInt(product.quantity - initial_quantity)
  
        if(product.quantity > initial_quantity){ 
          console.log("delta positive",product.name)
          console.log(shoppingList)
          shoppingList.inc_or_add_item(product.name, Math.abs(delta), userid);
        }
        else if(product.quantity < initial_quantity){
          console.log("delta negative",product.name)
          shoppingList.dec_item(product.name, Math.abs(delta), userid);
        }


        
        let items = {}
        shoppingList.items.forEach((value, key) => {

          
          items[key] = {
            pos: value.pos.counter,
            neg: value.neg.counter
          }});
        console.log({"uuid":shoppingList.uuid, "items":items})
        console.log(items)

        saveShoppingList(userid, id, {
          uuid: id,
          items: items
        }); 

      }
      )
  };
  const syncServer = () => {
    console.log("syncing to server")
  
    console.log("sending",shoppingList.toString())

    ipcRenderer.send('frontMessage', {body: shoppingList.toString(), type: "POST"});
    
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
          type='button'
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
                <th >Quantity</th>
              
  
                <th >Action</th>
             
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
                  
                  
                  <td className="actions" data-th="" style={{ width: "10%" }}>
                    
                        <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleRemoveProduct(product.name)} // Handle remove when button is clicked
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
                  <a href="#home" className="btn btn-info text-white">
                    Go Back
                  </a>
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


