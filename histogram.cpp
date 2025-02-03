#include <iostream>
#include <vector>

const int ARRAY_SIZE = 10;

int main() {
    // Create a large array
    std::vector<int> arr(ARRAY_SIZE, 0);

    // Access the array elementscd in a pattern that may cause cache thrashing
    for (int i = 0; i < ARRAY_SIZE; ++i) {
        // Alternate accessing elements with large strides
        for (int j = 0; j < ARRAY_SIZE; j += 1024) {
            arr[j] += i;
        }
    }

    // Sum up all elements to prevent optimization
    int sum = 0;
    for (int i = 0; i < ARRAY_SIZE; ++i) {
        sum += arr[i];
    }

    // Print the sum (to prevent compiler optimization)
    std::cout << "Sum: " << sum << std::endl;

    return 0;
}
