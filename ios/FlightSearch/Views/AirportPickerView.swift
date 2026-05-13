import SwiftUI

// MARK: - Airport Picker Sheet

struct AirportPickerView: View {
    let field: SearchViewModel.AirportField
    @Bindable var viewModel: SearchViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""

    var body: some View {
        NavigationStack {
            List {
                if viewModel.isLoadingAirports {
                    HStack {
                        Spacer()
                        ProgressView("Searching…")
                        Spacer()
                    }
                    .listRowSeparator(.hidden)

                } else if searchText.isEmpty {
                    quickSuggestionsSection

                } else if viewModel.airportSuggestions.isEmpty {
                    ContentUnavailableView(
                        "No airports found",
                        systemImage: "airplane.slash",
                        description: Text(
                            "Try an IATA code (JFK), city (Miami), " +
                            "metro alias (NYC), or region (caribbean)"
                        )
                    )
                } else {
                    Section {
                        ForEach(viewModel.airportSuggestions) { airport in
                            Button {
                                viewModel.selectAirport(airport, for: field)
                                dismiss()
                            } label: {
                                AirportRow(airport: airport)
                            }
                            .foregroundStyle(.primary)
                        }
                    } header: {
                        Text("\(viewModel.airportSuggestions.count) result\(viewModel.airportSuggestions.count == 1 ? "" : "s")")
                            .textCase(nil)
                    }
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle(field == .origin ? "From" : "To")
            .navigationBarTitleDisplayMode(.large)
            .searchable(
                text: $searchText,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: field == .origin
                    ? "ORD, Chicago, midwest…"
                    : "NYC, JFK, caribbean, canada…"
            )
            .onChange(of: searchText) { _, newValue in
                viewModel.lookupAirports(query: newValue)
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }

    // MARK: - Quick suggestions before the user types

    @ViewBuilder
    private var quickSuggestionsSection: some View {
        Section("Popular") {
            ForEach(quickSuggestions, id: \.self) { suggestion in
                Button {
                    searchText = suggestion
                    viewModel.lookupAirports(query: suggestion)
                } label: {
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundStyle(.secondary)
                            .frame(width: 24)
                        Text(suggestion)
                    }
                }
                .foregroundStyle(.primary)
            }
        }

        Section("Regions") {
            ForEach(regionSuggestions, id: \.self) { region in
                Button {
                    searchText = region
                    viewModel.lookupAirports(query: region)
                } label: {
                    HStack {
                        Image(systemName: "map")
                            .foregroundStyle(.blue)
                            .frame(width: 24)
                        Text(region.capitalized)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .foregroundStyle(.primary)
            }
        }
    }

    private var quickSuggestions: [String] {
        field == .origin
            ? ["ORD", "MDW", "Chicago", "New York", "Los Angeles", "Miami"]
            : ["NYC", "JFK", "MIA", "LAX", "CUN", "SJU"]
    }

    private var regionSuggestions: [String] {
        ["northeast", "southeast", "midwest", "west", "canada", "mexico",
         "caribbean", "puerto_rico"]
    }
}

// MARK: - Single airport row

struct AirportRow: View {
    let airport: Airport

    var body: some View {
        HStack(spacing: 12) {
            Text(airport.iata)
                .font(.system(.headline, design: .monospaced))
                .foregroundStyle(.blue)
                .frame(width: 48, alignment: .leading)

            VStack(alignment: .leading, spacing: 2) {
                Text(airport.city)
                    .font(.body)
                if !airport.name.isEmpty {
                    Text(airport.name)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            if airport.isInternational {
                Label("International", systemImage: "globe")
                    .labelStyle(.iconOnly)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .contentShape(Rectangle())
    }
}

#Preview("Airport Picker") {
    AirportPickerView(
        field: .destination,
        viewModel: SearchViewModel()
    )
}
