import Foundation

enum APIConfig {
    #if DEBUG
    /// Point at local uvicorn server during development.
    /// Run: uvicorn server:app --reload --port 8000
    static let baseURL = "http://localhost:8000"
    #else
    static let baseURL = "https://flight-price-optimizer.onrender.com"
    #endif

    static let pollIntervalSeconds: Double = 2.0
    static let requestTimeoutSeconds: Double = 15.0
}
