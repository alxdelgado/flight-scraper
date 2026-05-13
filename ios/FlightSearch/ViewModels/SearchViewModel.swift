import Foundation
import Observation

// MARK: - Search phase state machine

enum SearchPhase: Equatable {
    case idle
    case searching
    case complete
    case failed(String)

    var isSearching: Bool { self == .searching }
    var isComplete:  Bool { self == .complete  }

    static func == (lhs: SearchPhase, rhs: SearchPhase) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.searching, .searching), (.complete, .complete):
            return true
        case (.failed(let a), .failed(let b)):
            return a == b
        default:
            return false
        }
    }
}

// MARK: - ViewModel

@Observable
@MainActor
final class SearchViewModel {

    // MARK: Inputs
    var originCode:      String = ""
    var destinationQuery: String = ""
    var departDate:      Date   = Date()
    var returnDate:      Date?  = nil
    var isRoundTrip:     Bool   = true

    // MARK: Progress
    var searchPhase:        SearchPhase = .idle
    var completedSessions:  Int  = 0
    var totalSessions:      Int  = 0

    // MARK: Results
    var searchResult:    SearchStatusResponse?
    var errorMessage:    String?

    // MARK: Airport picker
    var airportSuggestions: [Airport] = []
    var isLoadingAirports:  Bool = false

    private let network: NetworkService
    private var pollingTask: Task<Void, Never>?

    init(network: NetworkService = .shared) {
        self.network = network
    }

    // MARK: - Search

    func startSearch() {
        guard !originCode.isEmpty, !destinationQuery.isEmpty else {
            errorMessage = "Please enter an origin and destination."
            return
        }

        pollingTask?.cancel()
        searchPhase       = .searching
        completedSessions = 0
        totalSessions     = 0
        searchResult      = nil
        errorMessage      = nil

        let request = SearchRequest(
            origin:      originCode.uppercased(),
            destination: destinationQuery,
            departDate:  departDate.isoDateString,
            returnDate:  isRoundTrip ? returnDate?.isoDateString : nil
        )

        pollingTask = Task {
            do {
                let created = try await network.createSearch(request)
                totalSessions = created.totalSessions
                await pollUntilComplete(searchId: created.searchId)
            } catch {
                searchPhase  = .failed(error.localizedDescription)
                errorMessage = error.localizedDescription
            }
        }
    }

    func cancelSearch() {
        pollingTask?.cancel()
        pollingTask  = nil
        searchPhase  = .idle
        errorMessage = nil
    }

    // MARK: - Airport lookup

    func lookupAirports(query: String) {
        guard query.count >= 2 else {
            airportSuggestions = []
            return
        }
        isLoadingAirports = true
        Task {
            do {
                airportSuggestions = try await network.resolveAirports(query: query)
            } catch {
                airportSuggestions = []
            }
            isLoadingAirports = false
        }
    }

    func selectAirport(_ airport: Airport, for field: AirportField) {
        switch field {
        case .origin:
            originCode = airport.iata
        case .destination:
            destinationQuery = airport.iata
        }
        airportSuggestions = []
    }

    enum AirportField { case origin, destination }

    // MARK: - Private

    private func pollUntilComplete(searchId: String) async {
        while !Task.isCancelled {
            do {
                let status = try await network.pollSearch(id: searchId)
                completedSessions = status.completedSessions
                totalSessions     = max(totalSessions, status.totalSessions)

                switch status.status {
                case .complete:
                    searchResult = status
                    searchPhase  = .complete
                    return
                case .failed:
                    let msg = status.error ?? "Search failed."
                    searchPhase  = .failed(msg)
                    errorMessage = msg
                    return
                case .running:
                    break
                }
            } catch {
                searchPhase  = .failed(error.localizedDescription)
                errorMessage = error.localizedDescription
                return
            }

            try? await Task.sleep(for: .seconds(APIConfig.pollIntervalSeconds))
        }
    }
}

// MARK: - Date formatting helper

private extension Date {
    var isoDateString: String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: self)
    }
}
