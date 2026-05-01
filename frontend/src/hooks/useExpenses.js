import { useEffect, useState, useCallback } from 'react'
import api from '../api/client.js'

export function useExpenses(month) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = month ? { month } : {}
      const r = await api.get('/expenses', { params })
      setData(r.data)
    } catch (e) {
      setError(e.message || 'Failed to load expenses')
    } finally {
      setLoading(false)
    }
  }, [month])

  useEffect(() => {
    reload()
  }, [reload])

  const create = async (payload) => {
    const r = await api.post('/expenses', payload)
    await reload()
    return r.data
  }
  const update = async (id, payload) => {
    const r = await api.put(`/expenses/${id}`, payload)
    await reload()
    return r.data
  }
  const remove = async (id) => {
    await api.delete(`/expenses/${id}`)
    await reload()
  }

  return { data, loading, error, reload, create, update, remove }
}
