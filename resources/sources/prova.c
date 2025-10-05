#include<stdio.h>
#include <stdlib.h>

struct riga{
int n1;
int n2;
int n3;
int n4;
int n5;
int n6;
int n7;
int n8;
int n9;
int n10;	
}*p;


int main(int argc, char *argv[])
{
FILE*file;
int i,j,count,m=0,r=0,a=1,N,num1,max[100],maxx,minn,min[100],somma[100];
struct riga temp;

if(!(file=fopen(argv[1],"r")))
{
	perror(argv[1]);
	exit(1);
}
char s[100];
p=malloc(sizeof(s));

while(fgets(s,sizeof(s),file)!=NULL)
{
	if(s[0]!='\n')
	{
		r++;
		if(a==r)
		{
			a=a*2;
			p=realloc(p,a*sizeof(s));
		}
		sscanf(s,"%i %i %i %i %i %i %i %i %i %i",
		&p[i].n1,&p[i].n2,&p[i].n3,&p[i].n4,&p[i].n5,&p[i].n6,&p[i].n7,&p[i].n8,&p[i].n9,&p[i].n10);
		i++;
	}
	p=realloc(p,r*sizeof(s));
}
//punto 1

printf("[CONTRARIO]\n");
	for(i=r;i>=0;i--)
	{
		printf("%i %i %i %i %i %i %i %i %i %i\n",
		p[i].n10,p[i].n9,p[i].n8,p[i].n7,p[i].n6,p[i].n5,p[i].n4,p[i].n3,p[i].n2,p[i].n1);
	}

//punto2

printf("[DISTRIBUZIONE]\n");
for(i=0;i<r;i++)
{
	for(j=-100;j<100;j++)
	{
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}	
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
		if(p[i].n1==j)
		{
			count++;
		}
	if(count>m)
	{
	m=count;
	num1=j;	
	}			
				
	}
	
}
printf("%i\n",num1);


//punto 3

for(i=0;i<r;i++)
{
	if(p[i].n1==p[i+1].n1 || p[i].n1==p[i+1].n2 || p[i].n1==p[i+1].n3 || p[i].n1==p[i+1].n4 || p[i].n1==p[i+1].n5 || 
	p[i].n1==p[i+1].n6 || p[i].n1==p[i+1].n7 || p[i].n1==p[i+1].n8 || p[i].n1==p[i+1].n9 || p[i].n1==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n2==p[i+1].n1 || p[i].n2==p[i+1].n1 || p[i].n2==p[i+1].n3 || p[i].n2==p[i+1].n4 || p[i].n2==p[i+1].n5 || 
		p[i].n2==p[i+1].n6 || p[i].n2==p[i+1].n7 || p[i].n2==p[i+1].n8 || p[i].n2==p[i+1].n9 || p[i].n2==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n3==p[i+1].n1 || p[i].n3==p[i+1].n2 || p[i].n3==p[i+1].n1 || p[i].n3==p[i+1].n4 || p[i].n3==p[i+1].n5 || 
		p[i].n3==p[i+1].n6 || p[i].n3==p[i+1].n7 || p[i].n3==p[i+1].n8 || p[i].n3==p[i+1].n9 || p[i].n3==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n4==p[i+1].n1 || p[i].n4==p[i+1].n2 || p[i].n4==p[i+1].n3 || p[i].n4==p[i+1].n1 || p[i].n4==p[i+1].n5 || 
		p[i].n4==p[i+1].n6 || p[i].n4==p[i+1].n7 || p[i].n4==p[i+1].n8 || p[i].n4==p[i+1].n9 || p[i].n4==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n5==p[i+1].n1 || p[i].n5==p[i+1].n2 || p[i].n5==p[i+1].n3 || p[i].n5==p[i+1].n4 || p[i].n5==p[i+1].n1 || 
		p[i].n5==p[i+1].n6 || p[i].n5==p[i+1].n7 || p[i].n5==p[i+1].n8 || p[i].n5==p[i+1].n9 || p[i].n5==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n6==p[i+1].n1 || p[i].n6==p[i+1].n2 || p[i].n6==p[i+1].n3 || p[i].n6==p[i+1].n4 || p[i].n6==p[i+1].n5 || 
		p[i].n6==p[i+1].n1 || p[i].n6==p[i+1].n7 || p[i].n6==p[i+1].n8 || p[i].n6==p[i+1].n9 || p[i].n6==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n7==p[i+1].n1 || p[i].n7==p[i+1].n2 || p[i].n7==p[i+1].n3 || p[i].n7==p[i+1].n4 || p[i].n7==p[i+1].n5 || 
		p[i].n7==p[i+1].n6 || p[i].n7==p[i+1].n1 || p[i].n7==p[i+1].n8 || p[i].n7==p[i+1].n9 || p[i].n7==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n8==p[i+1].n1 || p[i].n8==p[i+1].n2 || p[i].n8==p[i+1].n3 || p[i].n8==p[i+1].n4 || p[i].n8==p[i+1].n5 || 
		p[i].n8==p[i+1].n6 || p[i].n8==p[i+1].n7 || p[i].n8==p[i+1].n1 || p[i].n8==p[i+1].n9 || p[i].n8==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n9==p[i+1].n1 || p[i].n9==p[i+1].n2 || p[i].n9==p[i+1].n3 || p[i].n9==p[i+1].n4 || p[i].n9==p[i+1].n5 || 
		p[i].n9==p[i+1].n6 || p[i].n9==p[i+1].n7 || p[i].n9==p[i+1].n8 || p[i].n9==p[i+1].n1 || p[i].n9==p[i+1].n10)
	{
	N++;		
	}
	if(p[i].n10==p[i+1].n1 || p[i].n10==p[i+1].n2 || p[i].n10==p[i+1].n3 || p[i].n10==p[i+1].n4 || p[i].n10==p[i+1].n5 || 
		p[i].n10==p[i+1].n6 || p[i].n10==p[i+1].n7 || p[i].n10==p[i+1].n8 || p[i].n10==p[i+1].n9 || p[i].n10==p[i+1].n1)
	{
	N++;		
	}
									
}

printf("[NRIGHE]\n");
printf("%d\n",N);

//punto 4

printf("[MIN-MAX]\n");
for(i=0;i<r;i++)
{
	if(p[i].n1>p[i].n2 && p[i].n1>p[i].n3 && p[i].n1>p[i].n4 && p[i].n1>p[i].n5 && p[i].n1>p[i].n6 && 
	p[i].n1>p[i].n7 && p[i].n1>p[i].n8 && p[i].n1>p[i].n9 && p[i].n1>p[i].n10 )
	{
	max[i]=p[i].n1;	
	}
		if(p[i].n2>p[i].n1 && p[i].n2>p[i].n3 && p[i].n2>p[i].n4 && p[i].n2>p[i].n5 && p[i].n2>p[i].n6 && 
	p[i].n2>p[i].n7 && p[i].n2>p[i].n8 && p[i].n2>p[i].n9 && p[i].n2>p[i].n10 )
	{
	max[i]=p[i].n2;	
	}
		if(p[i].n3>p[i].n2 && p[i].n3>p[i].n1 && p[i].n3>p[i].n4 && p[i].n3>p[i].n5 && p[i].n3>p[i].n6 && 
	p[i].n3>p[i].n7 && p[i].n3>p[i].n8 && p[i].n3>p[i].n9 && p[i].n3>p[i].n10 )
	{
	max[i]=p[i].n3;	
	}
		if(p[i].n4>p[i].n2 && p[i].n4>p[i].n3 && p[i].n4>p[i].n1 && p[i].n4>p[i].n5 && p[i].n4>p[i].n6 && 
	p[i].n4>p[i].n7 && p[i].n4>p[i].n8 && p[i].n4>p[i].n9 && p[i].n4>p[i].n10 )
	{
	max[i]=p[i].n4;	
	}
		if(p[i].n5>p[i].n2 && p[i].n5>p[i].n3 && p[i].n5>p[i].n4 && p[i].n5>p[i].n1 && p[i].n5>p[i].n6 && 
	p[i].n5>p[i].n7 && p[i].n5>p[i].n8 && p[i].n5>p[i].n9 && p[i].n5>p[i].n10 )
	{
	max[i]=p[i].n5;	
	}
		if(p[i].n6>p[i].n2 && p[i].n6>p[i].n3 && p[i].n6>p[i].n4 && p[i].n6>p[i].n5 && p[i].n6>p[i].n1 && 
	p[i].n6>p[i].n7 && p[i].n6>p[i].n8 && p[i].n6>p[i].n9 && p[i].n6>p[i].n10 )
	{
	max[i]=p[i].n6;	
	}
		if(p[i].n7>p[i].n2 && p[i].n7>p[i].n3 && p[i].n7>p[i].n4 && p[i].n7>p[i].n5 && p[i].n7>p[i].n6 && 
	p[i].n7>p[i].n1 && p[i].n1>p[i].n8 && p[i].n7>p[i].n9 && p[i].n7>p[i].n10 )
	{
	max[i]=p[i].n7;	
	}
		if(p[i].n8>p[i].n2 && p[i].n8>p[i].n3 && p[i].n8>p[i].n4 && p[i].n8>p[i].n5 && p[i].n8>p[i].n6 && 
	p[i].n8>p[i].n7 && p[i].n8>p[i].n1 && p[i].n8>p[i].n9 && p[i].n8>p[i].n10 )
	{
	max[i]=p[i].n8;	
	}
		if(p[i].n9>p[i].n2 && p[i].n9>p[i].n3 && p[i].n9>p[i].n4 && p[i].n9>p[i].n5 && p[i].n9>p[i].n6 && 
	p[i].n9>p[i].n7 && p[i].n9>p[i].n8 && p[i].n9>p[i].n1 && p[i].n9>p[i].n10 )
	{
	max[i]=p[i].n9;	
	}
		if(p[i].n10>p[i].n2 && p[i].n10>p[i].n3 && p[i].n10>p[i].n4 && p[i].n10>p[i].n5 && p[i].n10>p[i].n6 && 
	p[i].n10>p[i].n7 && p[i].n10>p[i].n8 && p[i].n10>p[i].n9 && p[i].n10>p[i].n1 )
	{
	max[i]=p[i].n10;
	}
	if(max[i]>max[i-1])
	{
		maxx=max[i];
	}
}
for(i=0;i<r;i++)
{
	if(p[i].n1<p[i].n2 && p[i].n1<p[i].n3 && p[i].n1<p[i].n4 && p[i].n1<p[i].n5 && p[i].n1<p[i].n6 && 
	p[i].n1<p[i].n7 && p[i].n1<p[i].n8 && p[i].n1<p[i].n9 && p[i].n1<p[i].n10 )
	{
	min[i]=p[i].n1;	
	}
		if(p[i].n2<p[i].n1 && p[i].n2<p[i].n3 && p[i].n2<p[i].n4 && p[i].n2<p[i].n5 && p[i].n2<p[i].n6 && 
	p[i].n2<p[i].n7 && p[i].n2<p[i].n8 && p[i].n2<p[i].n9 && p[i].n2<p[i].n10 )
	{
	min[i]=p[i].n2;	
	}
		if(p[i].n3<p[i].n2 && p[i].n3<p[i].n1 && p[i].n3<p[i].n4 && p[i].n3<p[i].n5 && p[i].n3<p[i].n6 && 
	p[i].n3<p[i].n7 && p[i].n3<p[i].n8 && p[i].n3<p[i].n9 && p[i].n3<p[i].n10 )
	{
	min[i]=p[i].n3;	
	}
		if(p[i].n4<p[i].n2 && p[i].n4<p[i].n3 && p[i].n4<p[i].n1 && p[i].n4<p[i].n5 && p[i].n4<p[i].n6 && 
	p[i].n4<p[i].n7 && p[i].n4<p[i].n8 && p[i].n4<p[i].n9 && p[i].n4<p[i].n10 )
	{
	min[i]=p[i].n4;	
	}
		if(p[i].n5<p[i].n2 && p[i].n5<p[i].n3 && p[i].n5<p[i].n4 && p[i].n5<p[i].n1 && p[i].n5<p[i].n6 && 
	p[i].n5<p[i].n7 && p[i].n5<p[i].n8 && p[i].n5<p[i].n9 && p[i].n5<p[i].n10 )
	{
	min[i]=p[i].n5;	
	}
		if(p[i].n6<p[i].n2 && p[i].n6<p[i].n3 && p[i].n6<p[i].n4 && p[i].n6<p[i].n5 && p[i].n6<p[i].n1 && 
	p[i].n6<p[i].n7 && p[i].n6<p[i].n8 && p[i].n6<p[i].n9 && p[i].n6<p[i].n10 )
	{
	min[i]=p[i].n6;	
	}
		if(p[i].n7<p[i].n2 && p[i].n7<p[i].n3 && p[i].n7<p[i].n4 && p[i].n7<p[i].n5 && p[i].n7<p[i].n6 && 
	p[i].n7<p[i].n1 && p[i].n1<p[i].n8 && p[i].n7<p[i].n9 && p[i].n7<p[i].n10 )
	{
	min[i]=p[i].n7;	
	}
		if(p[i].n8<p[i].n2 && p[i].n8<p[i].n3 && p[i].n8<p[i].n4 && p[i].n8<p[i].n5 && p[i].n8<p[i].n6 && 
	p[i].n8<p[i].n7 && p[i].n8<p[i].n1 && p[i].n8<p[i].n9 && p[i].n8<p[i].n10 )
	{
	min[i]=p[i].n8;	
	}
		if(p[i].n9<p[i].n2 && p[i].n9<p[i].n3 && p[i].n9<p[i].n4 && p[i].n9<p[i].n5 && p[i].n9<p[i].n6 && 
	p[i].n9<p[i].n7 && p[i].n9<p[i].n8 && p[i].n9<p[i].n1 && p[i].n9<p[i].n10 )
	{
	min[i]=p[i].n9;	
	}
		if(p[i].n10<p[i].n2 && p[i].n10<p[i].n3 && p[i].n10<p[i].n4 && p[i].n10<p[i].n5 && p[i].n10<p[i].n6 && 
	p[i].n10<p[i].n7 && p[i].n10<p[i].n8 && p[i].n10<p[i].n9 && p[i].n10<p[i].n1 )
	{
	min[i]=p[i].n10;
	}
	if(min[i+1]<min[i])
	{
		minn=min[i];
	}
}
printf("%d\n",minn);
printf("%d\n",maxx);

//punto 5

int temps,som2;
printf("[ORDINAMENTO]\n");
for(i=0;i<r;i++)
{
	somma[i]=	p[i].n1+p[i].n2+p[i].n3+p[i].n4+p[i].n5+p[i].n6+p[i].n7+p[i].n8+p[i].n9+p[i].n10;
	som2=(p[i+1].n1+p[i+1].n2+p[i+1].n3+p[i+1].n4+p[i+1].n5+p[i+1].n6+p[i+1].n7+p[i+1].n8+p[i+1].n9+p[i+1].n10);
	if(som2<somma[i])
	{	
		temp=p[i+1];
		p[i+1]=p[i];
		p[i]=temp;
		temps=som2;
		som2=somma[i];
		somma[i]=temps;
	}
	
	}
for(i=0;i<r;i++)
{
	printf("%i %i %i %i %i %i %i %i %i %i (%i)\n",
		p[i].n1,p[i].n2,p[i].n3,p[i].n4,p[i].n5,p[i].n6,p[i].n7,p[i].n8,p[i].n9,p[i].n10,somma[i]);
}
	
}






