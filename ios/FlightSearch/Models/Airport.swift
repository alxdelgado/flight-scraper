import Foundation

struct Airport: Decodable, Identifiable, Hashable {
    let iata: String
    let name: String
    let city: String
    let subdivision: String
    let country: String
    let region: String
    let isInternational: Bool

    var id: String { iata }

    /// Display string shown in the airport picker list.
    var displayName: String {
        subdivision.isEmpty ? "\(city) (\(iata))" : "\(city), \(subdivision) (\(iata))"
    }

    enum CodingKeys: String, CodingKey {
        case iata, name, city, subdivision, country, region
        case isInternational = "is_international"
    }
}

// MARK: - API response wrappers

struct AirportQueryResponse: Decodable {
    let query: String
    let airports: [Airport]
}

struct AirportGroupedResponse: Decodable {
    let grouped: [String: [Airport]]
}
