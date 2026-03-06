import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('token')
        if (token) {
            fetchMe()
        } else {
            setLoading(false)
        }
    }, [])

    const fetchMe = async () => {
        try {
            const { data } = await api.get('/api/auth/me')
            setUser(data)
        } catch (error) {
            localStorage.removeItem('token')
            localStorage.removeItem('refresh')
            setUser(null)
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        const { data } = await api.post('/api/auth/login', { email, password })
        localStorage.setItem('token', data.access)
        localStorage.setItem('refresh', data.refresh)
        await fetchMe()
    }

    const registerNormal = async (formData) => {
        const { data } = await api.post('/api/auth/register/normal', formData)
        localStorage.setItem('token', data.access)
        localStorage.setItem('refresh', data.refresh)
        await fetchMe()
    }

    const registerHR = async (formData) => {
        const { data } = await api.post('/api/auth/register/hr', formData)
        localStorage.setItem('token', data.access)
        localStorage.setItem('refresh', data.refresh)
        await fetchMe()
    }

    const logout = async () => {
        try {
            const refresh = localStorage.getItem('refresh')
            if (refresh) {
                await api.post('/api/auth/logout', { refresh })
            }
        } catch (e) {
            // ignore
        }
        localStorage.removeItem('token')
        localStorage.removeItem('refresh')
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{ user, loading, login, registerNormal, registerHR, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext)
