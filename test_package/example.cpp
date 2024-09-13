// Simple TBB interface funcs

#include <stdio.h>
#include <iostream>
#include "oneapi/tbb/tick_count.h"

int main(int argc, char** argv)
{
	(void)argc; (void)argv;
    oneapi::tbb::tick_count t0 = oneapi::tbb::tick_count::now();
    std::cout << "TBB tick count resolution: " << t0.resolution() << std::endl;
    return 0;
}
