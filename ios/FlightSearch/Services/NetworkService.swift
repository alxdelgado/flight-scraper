import Foundation

// MARK: - Errors

enum NetworkError: LocalizedError {
    case invalidURL(String)
    case httpError(statusCode: Int, body: String)
    case decodingFailed(Error)
    case noData

    var errorDescription: String? {
        switch self {
        case .invalidURL(let url):
            return "Invalid URL: \(url)"
        case .httpError(let code, let body):
            return "Server error \(code): \(body)"
        case .decodingFailed(let error):
            return "Decoding failed: \(error.localizedDescription)"
        case .noData:
            return "No data received from server"
        }
    }
}

// MARK: - NetworkService

/// All communication with the Flight Price Optimizer API.
/// Inject a custom baseURL in tests; uses APIConfig.baseURL by default.
final class NetworkService {

    static let shared = NetworkService()

    private let baseURL: String
    private let session: URLSession

    init(baseURL: String = APIConfig.baseURL) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = APIConfig.requestTimeoutSeconds
        self.session = URLSession(configuration: config)
    }

    // MARK: - POST /search

    func createSearch(_ request: SearchRequest) async throws -> SearchCreatedResponse {
        let url = try makeURL("/search")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(request)
        return try await perform(req)
    }

    // MARK: - GET /search/{id}

    func pollSearch(id: String) async throws -> SearchStatusResponse {
        let url = try makeURL("/search/\(id)")
        return try await perform(URLRequest(url: url))
    }

    // MARK: - GET /airports

    func resolveAirports(query: String) async throws -> [Airport] {
        guard var components = URLComponents(string: baseURL + "/airports") else {
            throw NetworkError.invalidURL(baseURL + "/airports")
        }
        components.queryItems = [URLQueryItem(name: "q", value: query)]
        guard let url = components.url else {
            throw NetworkError.invalidURL(query)
        }
        let response: AirportQueryResponse = try await perform(URLRequest(url: url))
        return response.airports
    }

    func fetchAllAirports() async throws -> [String: [Airport]] {
        let url = try makeURL("/airports")
        let response: AirportGroupedResponse = try await perform(URLRequest(url: url))
        return response.grouped
    }

    // MARK: - GET /history

    func fetchHistory(limit: Int = 20) async throws -> [HistoryRun] {
        guard var components = URLComponents(string: baseURL + "/history") else {
            throw NetworkError.invalidURL(baseURL + "/history")
        }
        components.queryItems = [URLQueryItem(name: "limit", value: "\(limit)")]
        guard let url = components.url else {
            throw NetworkError.invalidURL("history")
        }
        let response: HistoryResponse = try await perform(URLRequest(url: url))
        return response.runs
    }

    // MARK: - GET /health

    func checkHealth() async throws -> HealthResponse {
        let url = try makeURL("/health")
        return try await perform(URLRequest(url: url))
    }

    // MARK: - Private helpers

    private func makeURL(_ path: String) throws -> URL {
        guard let url = URL(string: baseURL + path) else {
            throw NetworkError.invalidURL(baseURL + path)
        }
        return url
    }

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw NetworkError.noData
        }

        guard (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw NetworkError.httpError(statusCode: http.statusCode, body: body)
        }

        do {
            let decoder = JSONDecoder()
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decodingFailed(error)
        }
    }
}
