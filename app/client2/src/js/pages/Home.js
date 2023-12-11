import React, { useState, useEffect} from "react";
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import { fetchShoppingLists } from "../utils";
import ButtonGroup from '@mui/material/ButtonGroup';
const { ipcRenderer } = window.require('electron');
import { v4 as uuidv4 } from 'uuid';



const Home = () => {

    const errorMessage= "Error couldn't find it";
    const [error, setError] = useState(false); 

   

    // Listen for the response from the main process
    ipcRenderer.on('zmqMessage', (event, information) => {
        console.log('Received message from main process', information);
        if(information.body === errorMessage){
            setError(true);
        }else{
            setError(false);
            navigate(`/shopping-list/${shoppingListId}?type=remote`);
        }
    });
    

    
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

                const data = await fetchShoppingLists(userid);
                setShoppingLists(data);
            } catch (error) {
                console.error(error);
            }
        };
    
        const handleIdResponse = (event, id) => {
            console.log('Received ID:', id);
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
        const newId = uuidv4();

        setShoppingListId(newId);

        // Navigate to the new list URL
        navigate(`/shopping-list/${newId}?type=local`);
        
        
    };

    const handleShopingList = () => {
        ipcRenderer.send('frontMessage', {body: shoppingListId, type: "GET"});
        
        //navigate(`/shopping-list/${shoppingListId}`);
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
                        <Button key={shoppingList.uuid} onClick={() => navigate(`/shopping-list/${shoppingList.uuid}?type=local`)}>
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
            {error && <div className="alert alert-danger mt-3" role="alert">
                    Error: Shopping list not found.
            </div>}
                
        </div>
    );
};

export default Home;

