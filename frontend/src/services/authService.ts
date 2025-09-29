import { apiService } from './api'
import { User, LoginRequest, RefreshTokenRequest, ApiResponse } from '@/types'

class AuthService {
  private readonly endpoint = '/auth'

  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<{ user: User; tokens: { access_token: string; refresh_token: string; expires_in: number } }> {
    const response = await apiService.post<{ user: User; tokens: { access_token: string; refresh_token: string; expires_in: number } }>(`${this.endpoint}/login`, credentials)

    if (response) {
      const { tokens, user } = response
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      localStorage.setItem('user', JSON.stringify(user))

      // Set default authorization header for future requests
      if (tokens.access_token) {
        apiService['client'].defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`
      }
    }

    return response
  }

  /**
   * Refresh access token
   */
  async refreshToken(request: RefreshTokenRequest): Promise<{ access_token: string; expires_in: number }> {
    const response = await apiService.post<{ access_token: string; expires_in: number }>(`${this.endpoint}/refresh`, request)

    if (response) {
      const { access_token } = response
      localStorage.setItem('access_token', access_token)

      // Update authorization header
      apiService['client'].defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    }

    return response
  }

  /**
   * Logout user
   */
  async logout(): Promise<ApiResponse> {
    const refreshToken = localStorage.getItem('refresh_token')

    try {
      const response = await apiService.post<ApiResponse>(`${this.endpoint}/logout`, {
        refresh_token: refreshToken
      })

      return response
    } finally {
      // Always clean up local storage
      this.clearTokens()
    }
  }

  /**
   * Get current user from localStorage
   */
  getCurrentUser(): User | null {
    try {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    } catch {
      return null
    }
  }

  /**
   * Get access token from localStorage
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token')
  }

  /**
   * Get refresh token from localStorage
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getAccessToken()
    const user = this.getCurrentUser()
    return !!(token && user)
  }

  /**
   * Check if current user has specific permission
   */
  hasPermission(permission: string): boolean {
    const user = this.getCurrentUser()
    if (!user) return false

    return user.permissions.some(p =>
      p.resource === '*' || p.resource === permission.split(':')[0]
    )
  }

  /**
   * Check if current user has specific role
   */
  hasRole(role: string): boolean {
    const user = this.getCurrentUser()
    return user?.role === role
  }

  /**
   * Clear authentication tokens and user data
   */
  clearTokens(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')

    // Remove authorization header
    delete apiService['client'].defaults.headers.common['Authorization']
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<ApiResponse> {
    return apiService.put<ApiResponse>(`${this.endpoint}/profile`, updates)
  }

  /**
   * Change password
   */
  async changePassword(data: {
    current_password: string
    new_password: string
    confirm_password: string
  }): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/change-password`, data)
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/reset-password`, { email })
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: {
    token: string
    password: string
    confirm_password: string
  }): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/reset-password/confirm`, data)
  }

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/verify-email`, { token })
  }

  /**
   * Resend email verification
   */
  async resendVerification(): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/verify-email/resend`)
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/permissions`)
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    try {
      // Decode JWT token to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp < currentTime
    } catch {
      return true
    }
  }

  /**
   * Auto refresh token if needed
   */
  async ensureValidToken(): Promise<boolean> {
    if (!this.isAuthenticated()) {
      return false
    }

    if (this.isTokenExpired()) {
      const refreshToken = this.getRefreshToken()
      if (refreshToken) {
        try {
          await this.refreshToken({ refresh_token: refreshToken })
          return true
        } catch {
          this.clearTokens()
          return false
        }
      } else {
        this.clearTokens()
        return false
      }
    }

    return true
  }
}

// Export singleton instance
export const authService = new AuthService()

// Export class for testing
export { AuthService }