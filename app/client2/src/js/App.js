import React from 'react';
import {HashRouter,Route, Routes} from "react-router-dom";
import Home from './pages/Home';
import ShoppingList from './pages/ShoppingList';
import Login from './pages/Login';

const App = ()=> {
  return (
    <HashRouter>
        <Routes>
            <Route path="/" element={<Login/>}/>
            <Route path="/home" element={<Home/>}/>
            <Route path="/shopping-list/:id" element={<ShoppingList/>}/>
        </Routes>
    </HashRouter>    
  );
}

export default App;