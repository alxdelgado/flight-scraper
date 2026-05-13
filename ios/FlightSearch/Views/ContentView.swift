import SwiftUI

/// Root view — placeholder until Search + Results screens are built in Feature 5.
struct ContentView: View {
    @State private var viewModel = SearchViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Image(systemName: "airplane")
                    .font(.system(size: 64))
                    .foregroundStyle(.blue)

                Text("Flight Price Optimizer")
                    .font(.title2)
                    .fontWeight(.semibold)

                Text("Search screen coming in Feature 5")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .navigationTitle("Flights")
        }
    }
}

#Preview {
    ContentView()
}
