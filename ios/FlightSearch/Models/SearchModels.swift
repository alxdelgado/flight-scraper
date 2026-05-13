import Foundation

// MARK: - POST /search request

struct SearchRequest: Encodable {
    let origin: String
    let destination: String
    let departDate: String
    let returnDate: String?
    let maxDestinations: Int

    init(
        origin: String,
        destination: String,
        departDate: String,
        returnDate: String? = nil,
        maxDestinations: Int = 10
    ) {
        self.origin           = origin
        self.destination      = destination
        self.departDate       = departDate
        self.returnDate       = returnDate
        self.maxDestinations  = maxDestinations
    }

    enum CodingKeys: String, CodingKey {
        case origin, destination
        case departDate       = "depart_date"
        case returnDate       = "return_date"
        case maxDestinations  = "max_destinations"
    }
}

// MARK: - POST /search response

struct SearchCreatedResponse: Decodable {
    let searchId: String
    let status: String
    let totalSessions: Int

    enum CodingKeys: String, CodingKey {
        case searchId       = "search_id"
        case status
        case totalSessions  = "total_sessions"
    }
}

// MARK: - GET /search/{id} response

enum SearchStatusValue: String, Decodable {
    case running
    case complete
    case failed
}

struct SearchStatusResponse: Decodable {
    let searchId: String
    let status: SearchStatusValue
    let origin: String?
    let destination: String?
    let departDate: String?
    let returnDate: String?
    let completedSessions: Int
    let totalSessions: Int
    let winner: Candidate?
    let ranked: [Candidate]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case searchId           = "search_id"
        case status, origin, destination, error, winner, ranked
        case departDate         = "depart_date"
        case returnDate         = "return_date"
        case completedSessions  = "completed_sessions"
        case totalSessions      = "total_sessions"
    }

    var progressFraction: Double {
        guard totalSessions > 0 else { return 0 }
        return Double(completedSessions) / Double(totalSessions)
    }

    var progressLabel: String {
        "\(completedSessions) of \(totalSessions) airports searched"
    }
}

// MARK: - GET /history response

struct HistoryRun: Decodable, Identifiable {
    let id: Int
    let runAt: String
    let departDate: String
    let returnDate: String
    let winnerType: String?
    let winnerPrice: Double?

    enum CodingKeys: String, CodingKey {
        case id
        case runAt        = "run_at"
        case departDate   = "depart_date"
        case returnDate   = "return_date"
        case winnerType   = "winner_type"
        case winnerPrice  = "winner_price"
    }

    var winnerPriceFormatted: String {
        guard let p = winnerPrice else { return "--" }
        return String(format: "$%.2f", p)
    }
}

struct HistoryResponse: Decodable {
    let runs: [HistoryRun]
}

// MARK: - GET /health response

struct HealthResponse: Decodable {
    let status: String
    let db: String
    let version: String
}
