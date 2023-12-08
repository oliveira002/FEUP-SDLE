import React, { useState, useEffect} from "react";
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import { fetchShoppingLists } from "../utils";
import ButtonGroup from '@mui/material/ButtonGroup';
const { ipcRenderer } = window.require('electron');

const Home = () => {

   
    //ipcRenderer.send('frontMessage', {body: "shopping_list_1", type: "GET"});

    // Listen for the response from the main process
    ipcRenderer.on('zmqMessage', (event, information) => {
        console.log(JSON.stringify(information))
    // Do something with the information in your React component
    });


    console.log("username", localStorage.getItem("username"));
    
    let userid = '';
    const [shoppingListId, setShoppingListId] = useState('');
    const [shoppingLists, setShoppingLists] = useState(null);
    const [username, setUsername] = useState(localStorage.getItem("username"));
    if(shoppingLists){ 
        shoppingLists.ShoppingLists.map((shoppingList) => {
            console.log("shoppingList", shoppingList);
        })
      
    }

    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            console.log("fetching data");
            try {
                console.log("userid", userid);
                const data = await fetchShoppingLists(userid);
                setShoppingLists(data);
            } catch (error) {
                
            }
        };
    
        const handleIdResponse = (event, id) => {
            console.log('Received ID:', id);
           
            console.log("2");
            userid = id;
            fetchData(); 
            
         
        };
    
        ipcRenderer.send('getId', 'get id');
        ipcRenderer.on('getIdResponse', handleIdResponse);
    
        // Clean up the event listener when the component unmounts or when userid changes
        return () => {
            ipcRenderer.removeListener('getIdResponse', handleIdResponse);
        };
    }, []); 
 
    
    

  
    const handleNewList = () => {

        // Generate a new ID (for example, a random number for simplicity)
        const newId = Math.floor(Math.random() * 1000); // Generate a random number (replace this with your logic for generating IDs)
        
        // Redirect to the new list URL
        setShoppingListId(newId);
        console.log("newId", newId);
        // Navigate to the new list URL
        navigate(`/shopping-list/${newId}`);
        
        
    };

    const handleShopingList = () => {

        
        console.log("shoppingListId", shoppingListId);
        navigate(`/shopping-list/${shoppingListId}`);
    }


    return (
        <div>
        <AddShoppingCartIcon sx={{ fontSize: 40 }}/>
        <h1>Welcome {username}!</h1>
        <div className="shopping-lists home-button">
            <h3 >My Shopping Lists</h3>
            <ButtonGroup
                orientation="vertical"
                aria-label="vertical outlined button group"
            >
                {shoppingLists && shoppingLists.ShoppingLists && shoppingLists.ShoppingLists.length > 0 ? (
                    shoppingLists.ShoppingLists.map((shoppingList) => (
                        <Button key={shoppingList.uuid} onClick={() => navigate(`/shopping-list/${shoppingList.uuid}`)}>
                            Shopping List ID: {shoppingList.uuid}
                        </Button>
                    ))
                ) : (
                    <p>No local shopping lists</p>
                )}
            </ButtonGroup>
        </div>

        <Button className="home-button" onClick={handleNewList} variant="contained">Create New Shopping List</Button>
        <div className="shopping-lists">
        </div>
        
        <div className="shopping-row">
            <Box
                component="form"
                sx={{
                    '& .MuiTextField-root': { m: 1, width: '20ch' },
                }}
                noValidate
                autoComplete="off"
                >
                <div>
                    <TextField
                    type="text"
                    placeholder="Enter Shopping List ID"
                    value={shoppingListId}
                    onChange={(e) => setShoppingListId(e.target.value)}
                    
                    />
                
                </div>
                
            </Box>
            <div className="d-flex d-column justify-content-center align-items-center">
                <Button className="home-button"  variant="contained" onClick={handleShopingList} >
                    Enter Shopping List
                </Button>
            </div>
                
            </div>
        </div>
    );
};

export default Home;
