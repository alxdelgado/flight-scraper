import Foundation

struct Candidate: Decodable, Identifiable {
    let type: CandidateType
    let label: String
    let listedPrice: Double
    let baggageCost: Double
    let effectivePrice: Double
    let totalStops: Int
    let totalDuration: Int?
    let score: Double
    let airportsMatch: Bool
    let outbound: Flight?
    let returnFlight: Flight?
    let savings: Double?
    let savingsVs: String?

    var id: String { label }

    enum CandidateType: String, Decodable {
        case roundTrip   = "round-trip"
        case twoOneWays  = "two-one-ways"
    }

    enum CodingKeys: String, CodingKey {
        case type, label, score, outbound, savings
        case listedPrice    = "listed_price"
        case baggageCost    = "baggage_cost"
        case effectivePrice = "effective_price"
        case totalStops     = "total_stops"
        case totalDuration  = "total_duration"
        case airportsMatch  = "airports_match"
        case returnFlight   = "return"
        case savingsVs      = "savings_vs"
    }

    // MARK: - Display helpers

    var typeLabel: String {
        type == .roundTrip ? "Round-trip" : "Two one-ways"
    }

    var effectivePriceFormatted: String {
        String(format: "$%.2f", effectivePrice)
    }

    var baggageCostFormatted: String {
        baggageCost > 0 ? String(format: "+$%.0f bags", baggageCost) : "Incl."
    }

    var savingsFormatted: String? {
        guard let s = savings, s > 0, let vs = savingsVs else { return nil }
        return String(format: "Saves $%.2f vs %@", s, vs)
    }

    var mixedAirportNote: String? {
        guard type == .twoOneWays, !airportsMatch,
              let ob = outbound, let ret = returnFlight else { return nil }
        return "Arrive \(ob.destination), depart from \(ret.origin)"
    }
}
