import React, { useState } from "react";
import { checkLogin } from "../utils";
import { useNavigate } from "react-router-dom";

const Login = () => {
    const [username, setUsername] = useState("");
    const [svLogin, setSvLogin] = useState(null);
    const navigate = useNavigate(); // Use navigate from React Router
    const { ipcRenderer } = window.require('electron');
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            let user = await checkLogin(username);

            if (user) {
   
                setSvLogin("Login successful!");
                ipcRenderer.send('login', {body: user.id, type: "LOGIN"});
                localStorage.setItem("userid", user.id);
                localStorage.setItem("username", user.username);
                navigate('/home'); 

            } else {
                setSvLogin("Creating a new user!");
                //navigate('/home'); 

            }
        } catch (error) {
            console.error(error);
        }
        
    };

    return (
        <div className="container">
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="username" className="form-label">
                        Username
                    </label>
                    <input
                        type="text"
                        className="form-control"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>
                
                <button type="submit" className="btn btn-primary">
                    Submit
                </button>
            </form>
            {svLogin && (
                <div className="alert alert-success mt-3" role="alert">
                    {svLogin}
                </div>
            )}
        </div>
    );
};

export default Login;
