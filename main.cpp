#include <iostream>

int global = 12; //전역변수

int Add(int num1,int num2) //add함수이 호출되면서 생성 되는 변수들 지역변수
{
 return num1+num2;
}
int main() {
    //변수
    // 1. 지역변수 : 함수 안에서 정의된 변수들 다른 함수에서 사용 할려면 다른 코드가 필요하다
    // 2. 전역변수 : 함수 외부에 선언된 변수 다른 함수에서 사용 가능함
    // 3. 전적변수
    // 4. 외부변수
    using namespace std;

    //함수
    //이상적인 함수는 최소한의 기능을 모듈화 하여 필요한곳에 바로 불러올수있게 작성

    {//내부지역
        //변수명 규칙
            //같은지역내에 컴파일러가 구별 할수있게 위해 변수 명을 다르게 지정
            //또 함수안에 내부지역을 선언하면 거기에 다른지역이 생성됬기 때문에 컴파일러가 구별할 수 있다.

    }

    //지역변수
    //괄호 안에 선언된 변수(함수,지역)
    int data;
    data = Add(10,20);
    cout << data<<"\n";
    //반복문
    //countinue 반복자 변경으로 이동
    //break #반복문 나감
    //for (int i = 0; i < ; ++i) {}
    for (/*반복자 초기화*/ int i = 0; /*반복시 조건 체크 참 또는 거짓이 들어와야함*/ i<10;/*반복자 변경*/++i)
    {
        if (i % 2 == 1)
        {
            continue;
        }

        printf("%d\n",i);
    }
    //while ()

    int i = 0;

    while (i < 2) /*조건체크*/
    {
        printf("%d\n",i);
        ++i;
    }

    //printf
    //포매팅
    printf("abcdef%d\n",10);
    printf("abcdef%f\n",1.2151);
    char input[20];

    scanf("%s",input);
    printf("%s",input);



    return 0;
}
