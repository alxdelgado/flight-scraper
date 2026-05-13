import Foundation

struct Flight: Decodable, Hashable {
    let origin: String
    let destination: String
    let date: String
    let returnDate: String?
    let tripType: String
    let airline: String?
    let priceUsd: Double
    let stops: Int
    let durationMins: Int?
    let departureTime: String?
    let arrivalTime: String?
    let bookingUrl: String?

    enum CodingKeys: String, CodingKey {
        case origin, destination, date
        case returnDate     = "return_date"
        case tripType       = "trip_type"
        case airline
        case priceUsd       = "price_usd"
        case stops
        case durationMins   = "duration_mins"
        case departureTime  = "departure_time"
        case arrivalTime    = "arrival_time"
        case bookingUrl     = "booking_url"
    }

    // MARK: - Derived display helpers

    var formattedPrice: String {
        String(format: "$%.2f", priceUsd)
    }

    var formattedDuration: String {
        guard let mins = durationMins else { return "--" }
        let h = mins / 60
        let m = mins % 60
        return "\(h)h \(String(format: "%02d", m))m"
    }

    var stopsLabel: String {
        stops == 0 ? "Nonstop" : "\(stops) stop\(stops == 1 ? "" : "s")"
    }

    var routeLabel: String { "\(origin) → \(destination)" }

    var bookingLink: URL? {
        guard let raw = bookingUrl else { return nil }
        return URL(string: raw)
    }
}
